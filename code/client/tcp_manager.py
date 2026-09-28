"""
File Transfer Client
- Trasferimento a chunk con checksum CRC32 per ogni chunk
- Retry automatico su errore CRC
- Ripresa trasferimento (resume) in caso di disconnessione
- Verifica integrità finale SHA-256
"""

import os
import socket
from threading import Event
import time
import zlib

from pathlib import Path

import mysql

from client.manager import Manager
from client.paths import LOG_DIR, ZIP_DIR
from utils_funct.tcp_utility import recv_exact, recv_json, send_json, sha256_of_file


class tcp_client_manager(Manager):
    def __init__(self, config, stop_event : Event):
        super().__init__(config, stop_event)
        # Setup the logger
        self.logger = self.setup_logger("tcp_manager", LOG_DIR, "tcp_manager.log")

        self.completed_zip_path = os.path.join(ZIP_DIR, "Completed")

        self.host = config['SERVER_CONN']['ServerIP']
        self.port = int(config['SERVER_CONN']['Port'])
        self.chunk_size = 64 * 1024    # 64 KB per chunk
        self.max_retry = 5            # Tentativi massimi per chunk in caso di CRC error


    # ── Logica di invio ──────────────────────────────────────────────────────────

    def run(self):
        while True:
            try:
                zip_name = self.get_next_zip()
                if not zip_name:
                    self.logger.info('No file to send. Sleeping...')
                    time.sleep(10)
                    continue
                file_to_send = os.path.join(self.completed_zip_path, zip_name)
                success = self.send_file(file_to_send)
                if success:
                    os.remove(file_to_send)
                if not success:
                    self.logger.error(f'Errore durante l\'invio di {file_to_send}')
            except mysql.connector.Error as e:
                self.logger.error(f"Fatal error in TCP manager {e}")
                self.stop_event.set()  # avvisa il padre

    
    def get_next_zip(self):
        '''
        Returns:
            the name of the first zip folder, ascending order
        '''
        zip_files = sorted(os.listdir(self.completed_zip_path))
        
        return zip_files[0] if len(zip_files) != 0 else None

    def send_file(self, filepath: str) -> bool:
        path = Path(filepath)
        try:
            filesize = path.stat().st_size
        except FileNotFoundError:
            self.logger.error(f"File non trovato: {filepath}")
            return False  # errore recuperabile, il chiamante decide cosa fare
        
        try:
            self.logger.info(f'Calcolo SHA-256 di {path.name}...')
            sha256 = sha256_of_file(path)
            self.logger.info(f'SHA-256: {sha256}')

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))
                self.logger.info(f'Connesso a {self.host}:{self.port}')

                # ── 1. Handshake ─────────────────────────────────────────────────
                send_json(sock, {
                    'flexin_name': self.config['GENERAL']['FlexinName'],
                    'filename':   path.name,
                    'filesize':   filesize,
                    'sha256':     sha256,
                    'chunk_size': self.chunk_size,
                })

                ack = recv_json(sock)
                start_offset = ack.get('offset', 0)

                if ack['status'] == 'resume':
                    self.logger.info(f'Resume: il server ha già {start_offset} byte, riprendo da lì')
                else:
                    self.logger.info('Avvio trasferimento da zero')

                # ── 2. Invio chunk ───────────────────────────────────────────────
                total_chunks = (filesize + self.chunk_size - 1) // self.chunk_size
                sent_bytes   = start_offset

                with open(path, 'rb') as f:
                    f.seek(start_offset)
                    chunk_index = start_offset // self.chunk_size

                    while True:
                        data = f.read(self.chunk_size)
                        if not data:
                            break

                        offset  = chunk_index * self.chunk_size
                        crc32   = zlib.crc32(data) & 0xFFFFFFFF
                        retries = 0

                        while retries < self.max_retry:
                            # Invia header + dati
                            send_json(sock, {
                                'index':  chunk_index,
                                'offset': offset,
                                'size':   len(data),
                                'crc32':  crc32,
                            })
                            sock.sendall(data)

                            # Attendi ACK
                            ack = recv_json(sock)

                            if ack['status'] == 'ok':
                                sent_bytes += len(data)
                                pct = sent_bytes * 100 // filesize
                                self.logger.info(f'Chunk {chunk_index}/{total_chunks-1} inviato  ({pct}%)')
                                break
                            elif ack['status'] == 'crc_error':
                                retries += 1
                                self.logger.warning(f'CRC error chunk {chunk_index}, retry {retries}/{self.max_retry}')
                                time.sleep(0.2 * retries)
                            else:
                                self.logger.error(f'Errore server: {ack}')
                                return False
                        else:
                            self.logger.error(f'Chunk {chunk_index} fallito dopo {self.max_retry} tentativi. Aborto.')
                            return False

                        chunk_index += 1

                # ── 3. Segnala fine trasferimento ─────────────────────────────────
                send_json(sock, {'done': True})

                # ── 4. Risposta finale ────────────────────────────────────────────
                result = recv_json(sock)
                status = result.get('status')

                if status == 'complete':
                    self.logger.info('Trasferimento completato con successo e integrità verificata!')
                    return True
                elif status == 'sha256_mismatch':
                    self.logger.error('Il server ha rilevato un mismatch SHA-256. File rimosso (rollback).')
                    return False
                else:
                    self.logger.error(f'Errore inatteso dal server: {result}')
                    return False
                
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self.logger.error(f"Errore di rete durante l'invio di {path.name}: {e}")
            return False  # il chiamante sa che deve riprovare


