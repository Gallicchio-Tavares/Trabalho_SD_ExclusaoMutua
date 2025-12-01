# process.py -> cada processo envia requests, aguarda grant e escreve no arquivo
import socket
import time
from datetime import datetime
from common import *

HOST = "127.0.0.1"
PORT = 5000


def run_process(pid, r, k):
    sock = socket.socket()
    sock.connect((HOST, PORT))

    # Enviar PID ao conectar
    sock.send(build_message("0", pid))

    for _ in range(r):
        # Enviar REQUEST
        sock.send(build_message(MSG_REQUEST, pid))

        # Esperar GRANT
        while True:
            data = sock.recv(F)
            msg_id, recv_pid = parse_message(data)
            if msg_id == MSG_GRANT and recv_pid == pid:
                break

        # Região crítica
        now = datetime.now().strftime("%H:%M:%S.%f")
        with open("resultado.txt", "a") as f:
            f.write(f"PID {pid} | {now}\n")

        time.sleep(k)

        # Enviar RELEASE
        sock.send(build_message(MSG_RELEASE, pid))

    sock.close()
