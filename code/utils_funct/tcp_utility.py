import os
import hashlib
import json
import socket
import struct
from pathlib import Path

def send_json(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data).encode()
    sock.sendall(struct.pack('>I', len(payload)) + payload)
    

def recv_json(sock: socket.socket) -> dict:
    raw_len = recv_exact(sock, 4)
    length  = struct.unpack('>I', raw_len)[0]
    return json.loads(recv_exact(sock, length).decode())


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError('Connessione chiusa inaspettatamente')
        buf += chunk
    return buf


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    return h.hexdigest()