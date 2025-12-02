# run_experiment.py
import subprocess
import time
from multiprocessing import Process
from datetime import datetime
from process import run_process


def validate_log(n, r):
    """
    Função extra para validar se o resultado atende aos requisitos
    """
    print("\n--- Validando resultado.txt ---")
    try:
        with open("resultado.txt", "r") as f:
            lines = f.readlines()
        
        expected_lines = n * r
        print(f"Linhas esperadas: {expected_lines}")
        print(f"Linhas obtidas:   {len(lines)}")
        
        if len(lines) != expected_lines:
            print("FALHA: Número de linhas incorreto!")
        else:
            print("SUCESSO: Número de linhas correto.")

        # Verifica ordem cronológica
        last_time = datetime.min
        cronologia_ok = True
        counts = {}

        for line in lines:
            parts = line.strip().split(" | ")
            if len(parts) < 2: continue
            
            pid_str = parts[0].replace("PID ", "")
            timestamp = datetime.strptime(parts[1], "%H:%M:%S.%f")
            
            # Contagem por PID
            counts[pid_str] = counts.get(pid_str, 0) + 1

            if timestamp < last_time:
                print(f"FALHA: Violação de ordem cronológica na linha: {line.strip()}")
                cronologia_ok = False
            last_time = timestamp
            
        if cronologia_ok:
            print("SUCESSO: Ordem cronológica respeitada.")
            
        print(f"Execuções por PID: {counts}")
            
    except Exception as e:
        print(f"Erro na validação: {e}")


def run_experiment(n, r, k):
    open("resultado.txt", "w").close()

    print(f"Iniciando experimento: n={n}, r={r}, k={k}")

    procs = []
    for pid in range(1, n + 1):
        p = Process(target=run_process, args=(pid, r, k))
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    print("Experimento finalizado.")
    
    validate_log(n, r)


if __name__ == "__main__":
    run_experiment(n=5, r=3, k=1)
