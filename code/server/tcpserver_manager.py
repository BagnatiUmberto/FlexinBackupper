# ── Protocollo ──────────────────────────────────────────────────────────────
# Ogni messaggio è preceduto da 4 byte (big-endian uint32) che indicano
# la lunghezza del payload JSON o dei dati binari.
#
# Handshake:
#   CLIENT → SERVER:  { "filename": str, "filesize": int, "sha256": str,
#                        "chunk_size": int, "resume_offset": int }
#   SERVER → CLIENT:  { "status": "ok"|"resume", "offset": int }
#
# Trasferimento chunk (ripetuto):
#   CLIENT → SERVER:  header JSON  { "index": int, "offset": int, "size": int, "crc32": int }
#                     + dati binari (size byte)
#   SERVER → CLIENT:  { "status": "ok"|"crc_error"|"error", "index": int }
#
# Fine trasferimento:
#   CLIENT → SERVER:  { "done": true }
#   SERVER → CLIENT:  { "status": "complete"|"sha256_mismatch"|"error" }
# ────────────────────────────────────────────────────────────────────────────


import os
import shutil
import socket
import traceback
import zlib
from pathlib import Path

from utils_funct.tcp_utility import recv_exact, recv_json, send_json, sha256_of_file
from server.manager import Manager


class TCPServerManager(Manager):
    def __init__(self, config):
        super().__init__(config)
        print("Initializing TCPServerManager...")
        self.logger = self.setup_logger("tcp_server", "tcp_server.log")
        self.logger.info("TCPServerManager initialized")
        self.zip_dir = config["FOLDERS"]["Zips"]


    def run(self):        
        host = '0.0.0.0'
        port = 50007
        print(f'Avvio server TCP su {host}:{port}...')
        self.logger.info(f'In ascolto su porta {port}...')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:            
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind((host, port))
                srv.listen(5)
                self.logger.info(f'In ascolto su porta {port}...')

                while True:
                    print("In attesa di connessioni...")
                    conn, addr = srv.accept()
                    print(f"Connessione accettata {addr}")
                    self.handle_client(conn, addr)
        except Exception as e:
            print(f'Errore nel server TCP: {e}')
            self.logger.error(f'Errore nel server TCP: {e}')
            traceback.print_exc()

    def handle_client(self, conn: socket.socket, addr):
        self.logger.info(f'Connessione da {addr}')
        tmp_path  = None
        save_path = None

        try:
            # ── 1. Handshake ─────────────────────────────────────────────────
            meta = recv_json(conn)
            flexin_name = meta['flexin_name']
            filename   = Path(meta['filename']).name          # sicurezza: solo nome
            filesize   = meta['filesize']
            sha256_exp = meta['sha256']
            chunk_size = meta['chunk_size']


            received_dir = Path(self.zip_dir)/"received_files"/flexin_name
            temp_dir = Path(self.zip_dir)/"temp_transfers"/flexin_name

            os.makedirs(received_dir, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            save_path = Path(received_dir/filename)
            tmp_path = temp_dir / Path(filename).with_suffix('.part')

            # Se esiste già il file parziale eliminalo e ricomincia da capo
            if tmp_path.exists():
                os.remove(tmp_path)
            send_json(conn, {'status': 'ok', 'offset': 0})

            # ── 2. Ricezione chunk ───────────────────────────────────────────
            received = 0
            with open(tmp_path, 'ab') as f:
                while True:
                    msg = recv_json(conn)

                    if msg.get('done'):
                        break

                    idx    = msg['index']
                    offset = msg['offset']
                    size   = msg['size']
                    crc_ex = msg['crc32']

                    # Leggi i dati binari del chunk
                    data = recv_exact(conn, size)

                    # Verifica CRC32
                    crc_got = zlib.crc32(data) & 0xFFFFFFFF
                    if crc_got != crc_ex:
                        self.logger.warning(f'CRC32 mismatch chunk {idx}: atteso {crc_ex}, ottenuto {crc_got}')
                        send_json(conn, {'status': 'crc_error', 'index': idx})
                        continue   # Il client rimanderà il chunk

                    # Scrivi al posto giusto
                    f.seek(offset)
                    f.write(data)
                    f.flush()
                    received += size
                    #self.logger.info(f'Chunk {idx} OK  ({received}/{filesize} byte, {received*100//filesize}%)')
                    send_json(conn, {'status': 'ok', 'index': idx})

            # ── 3. Verifica SHA-256 finale ───────────────────────────────────
            self.logger.info('Verifica SHA-256 in corso...')
            sha256_got = sha256_of_file(tmp_path)

            if sha256_got != sha256_exp:
                self.logger.error(f'SHA-256 mismatch! Rollback di {tmp_path}')
                tmp_path.unlink(missing_ok=True)         # ← ROLLBACK
                send_json(conn, {'status': 'sha256_mismatch'})
                return

            # ── 4. Promozione file temporaneo → definitivo ───────────────────
            shutil.move(str(tmp_path), str(save_path))
            self.logger.info(f'File salvato in {save_path}')
            send_json(conn, {'status': 'complete'})

        except Exception as e:
            self.logger.error(f'Errore durante il trasferimento: {e}')
            # Rollback: elimina il file temporaneo corrotto
            if tmp_path and tmp_path.exists():
                self.logger.warning(f'Rollback: elimino {tmp_path}')
                tmp_path.unlink(missing_ok=True)
            try:
                send_json(conn, {'status': 'error', 'message': str(e)})
            except Exception:
                pass
        finally:
            conn.close()
            self.logger.info(f'Connessione chiusa con {addr}')