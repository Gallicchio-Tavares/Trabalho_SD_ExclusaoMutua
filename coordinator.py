# coordinator.py -> coordenador multithread, com conexão, lógica e interface
import socket
import threading
import queue
import logging
from datetime import datetime
from common import *

HOST = "127.0.0.1"
PORT = 5000

# Fila sincronizada
request_queue = queue.Queue()

# { pid: socket }
clients = {}

# Contador de vezes atendido
served_count = {}

# Mutex para acesso às estruturas
lock = threading.Lock()

# Logger
logging.basicConfig(
    filename="logs/coordinator.log",
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

def log_event(event):
    logging.info(event)


# ---------------------
# Thread 1: Conexões
# ---------------------
def connection_thread(sock):
    while True:
        client_socket, addr = sock.accept()
        pid = int(client_socket.recv(F).decode().split(SEP)[1])
        with lock:
            clients[pid] = client_socket
            served_count.setdefault(pid, 0)
        log_event(f"Novo processo conectado: PID {pid}")


# ---------------------
# Thread 2: Lógica centralizada
# ---------------------
def logic_thread():
    while True:
        # Verificar mensagens de todos os processos
        with lock:
            active_clients = list(clients.items())

        for pid, client_socket in active_clients:
            try:
                data = client_socket.recv(F)
                if not data:
                    continue
            except BlockingIOError:
                continue
            except ConnectionResetError:
                continue

            msg_id, sender_pid = parse_message(data)
            log_event(f"RECEBIDO | PID {sender_pid} | MSG {msg_id}")

            if msg_id == MSG_REQUEST:
                request_queue.put(sender_pid)

                # Se for o único na fila → envia GRANT
                if request_queue.qsize() == 1:
                    send_grant(sender_pid)

            elif msg_id == MSG_RELEASE:
                finished_pid = request_queue.get()
                served_count[finished_pid] += 1

                # Próximo da fila
                if not request_queue.empty():
                    next_pid = request_queue.queue[0]
                    send_grant(next_pid)



def send_grant(pid):
    with lock:
        sock = clients[pid]
    msg = build_message(MSG_GRANT, pid)
    sock.send(msg)
    log_event(f"ENVIADO | PID {pid} | GRANT")


# ---------------------
# Thread 3: Interface
# ---------------------
def interface_thread():
    while True:
        cmd = input().strip()

        if cmd == "fila":
            with lock:
                print("Fila atual:", list(request_queue.queue))

        elif cmd == "atendidos":
            with lock:
                print("Atendimentos:", served_count)

        elif cmd == "exit":
            print("Encerrando coordenador...")
            break


# ---------------------
# Main
# ---------------------
def main():
    server = socket.socket()
    server.bind((HOST, PORT))
    server.listen()

    print("Coordenador iniciado.")

    threading.Thread(target=connection_thread, args=(server,), daemon=True).start()
    threading.Thread(target=logic_thread, daemon=True).start()
    interface_thread()


if __name__ == "__main__":
    main()
