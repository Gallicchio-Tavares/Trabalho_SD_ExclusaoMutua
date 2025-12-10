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
    # Opcional: imprimir no terminal também para debug
    # print(event)


# ---------------------
# Thread 1: Conexões
# ---------------------
def connection_thread(sock):
    while True:
        client_socket, addr = sock.accept()
        
        client_socket.setblocking(True)
        try:
            data = client_socket.recv(F)
            if not data:
                client_socket.close()
                continue
            
            pid = int(data.decode().split(SEP)[1])
            
            # mudando pra NÃO-BLOQUEANTE
            client_socket.setblocking(False)
            
            with lock:
                clients[pid] = client_socket
                served_count.setdefault(pid, 0)
            log_event(f"Novo processo conectado: PID {pid}")
            
        except Exception as e:
            print(f"Erro na conexão inicial: {e}")
            client_socket.close()


# ---------------------
# Thread 2: Lógica centralizada
# ---------------------
def logic_thread():
    while True:
        # ver msgs de todos os processos
        with lock:
            active_clients = list(clients.items())

        for pid, client_socket in active_clients:
            try:
                data = client_socket.recv(F)
                
                # tratando desconexão
                if not data:
                    with lock:
                        if pid in clients:
                            print(f"Detectada desconexão do PID {pid}")
                            clients[pid].close()
                            del clients[pid]
                    continue

                msg_id, sender_pid = parse_message(data)
                log_event(f"RECEBIDO | PID {sender_pid} | MSG {msg_id}")

                if msg_id == MSG_REQUEST:
                    # Verifica se a fila estava vazia ANTES de inserir
                    with lock:
                        was_empty = request_queue.empty()
                        request_queue.put(sender_pid)
                    
                    # Se estava vazia, pode enviar GRANT imediatamente
                    if was_empty:
                        send_grant(sender_pid)

                elif msg_id == MSG_RELEASE:
                    next_pid = None
                    with lock:
                        if not request_queue.empty():
                            finished_pid = request_queue.get()
                            served_count[finished_pid] = served_count.get(finished_pid, 0) + 1

                        # Se ainda há alguém na fila, pega o próximo
                        if not request_queue.empty():
                            # Pega o próximo sem remover da fila
                            next_pid = request_queue.queue[0]
                    
                    # Envia GRANT fora do lock (para evitar deadlock)
                    if next_pid is not None:
                        send_grant(next_pid)

            except BlockingIOError:
                # Normal para sockets não-bloqueantes quando não há dados
                continue
            except ConnectionResetError:
                # Cliente caiu abruptamente
                with lock:
                    if pid in clients:
                        clients[pid].close()
                        del clients[pid]
                continue


def send_grant(pid):
    with lock:
        if pid in clients:
            sock = clients[pid]
            try:
                msg = build_message(MSG_GRANT, pid)
                sock.send(msg)
                log_event(f"ENVIADO | PID {pid} | GRANT")
            except Exception as e:
                print(f"Erro ao enviar GRANT para {pid}: {e}")


# ---------------------
# Thread 3: Interface
# ---------------------
def interface_thread():
    print("Interface ativa. Comandos: fila, atendidos, exit")
    while True:
        try:
            cmd = input().strip()
        except EOFError:
            break

        if cmd == "fila":
            with lock:
                print("Fila atual:", list(request_queue.queue))

        elif cmd == "atendidos":
            with lock:
                print("Atendimentos:", served_count)

        elif cmd == "exit":
            print("Encerrando coordenador...")
            # Fecha todos os sockets antes de sair
            with lock:
                for pid, sock in clients.items():
                    try:
                        sock.close()
                    except:
                        pass
            break


# ---------------------
# Main
# ---------------------
def main():
    # usando agr o SO_REUSEADDR pra evitar erro de "Address already in use" qnd reinicia rápido
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Coordenador iniciado em {HOST}:{PORT}.")

    threading.Thread(target=connection_thread, args=(server,), daemon=True).start()
    threading.Thread(target=logic_thread, daemon=True).start()
    interface_thread()


if __name__ == "__main__":
    main()