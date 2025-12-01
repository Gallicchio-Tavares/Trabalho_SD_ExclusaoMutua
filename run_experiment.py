# run_experiment.py
import subprocess
from multiprocessing import Process
from process import run_process


def run_experiment(n, r, k):
    # Limpa arquivo
    open("resultado.txt", "w").close()

    # Inicia n processos
    procs = []
    for pid in range(1, n + 1):
        p = Process(target=run_process, args=(pid, r, k))
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    print("Experimento finalizado.")


if __name__ == "__main__":
    run_experiment(n=5, r=3, k=1)
