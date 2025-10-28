#!/usr/bin/env python3
"""
tclab_onoff_7days.py

Gera dados simulados (modo gêmeo digital) das variáveis T1, T2, Q1, Q2 do TCLab
com amostragem de 1 segundo e controle ON/OFF.
"""

import os
# força simulação antes de importar o TCLab
os.environ["TCLAB_SIMULATE"] = "True"

import argparse
import csv
import json
import time
from datetime import datetime

try:
    from tclab import TCLabModel as TCLab

except ImportError:
    print("Instale com: pip install tclab")
    exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration-days', type=float, default=7.0, help='Duração em dias (padrão: 7)')
    parser.add_argument('--accelerate', type=float, default=1.0, help='Fator de aceleração (>1 = mais rápido)')
    parser.add_argument('--deadband', type=float, default=0.5, help='Deadband °C para controle ON/OFF')
    parser.add_argument('--output-prefix', type=str, default='tclab', help='Prefixo dos arquivos')
    return parser.parse_args()


def onoff_control(temp, setpoint, deadband, last_val):
    """Controlador ON/OFF com histerese"""
    if temp < setpoint - deadband:
        return 100
    elif temp > setpoint + deadband:
        return 0
    else:
        return last_val


def main():
    args = parse_args()
    total_seconds = int(args.duration_days * 24 * 3600)
    sleep_real = 1.0 / args.accelerate

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"{args.output_prefix}_{timestamp}.csv"
    json_file = f"{args.output_prefix}_{timestamp}.json"

    print(f"Modo simulado ativado (sem Arduino físico)")
    print(f"Simulação de {args.duration_days} dias ({total_seconds} segundos simulados)")
    print(f"Acelerando {args.accelerate}x -> tempo real por amostra: {sleep_real:.4f}s")

    rows = []

    # inicializa TCLab em modo simulado
    lab = TCLab()
    lab.Q1(0)
    lab.Q2(0)
    last_q1, last_q2 = 0, 0

    try:
        for t in range(total_seconds):
            T1, T2 = lab.T1, lab.T2

            # alterna setpoints a cada 12 horas
            sp1 = 25 + 5 * ((t // 43200) % 2)
            sp2 = 23 + 5 * ((t // 43200) % 2)

            q1 = onoff_control(T1, sp1, args.deadband, last_q1)
            q2 = onoff_control(T2, sp2, args.deadband, last_q2)
            lab.Q1(q1)
            lab.Q2(q2)

            last_q1, last_q2 = q1, q2

            rows.append({
                "time_s": t,
                "datetime": datetime.now().isoformat(),
                "T1": T1,
                "T2": T2,
                "Q1": q1,
                "Q2": q2,
                "SP1": sp1,
                "SP2": sp2
            })

            if t % 100 == 0:
                print(f"[{t}/{total_seconds}] T1={T1:.2f}C, T2={T2:.2f}C, SP1={sp1}, SP2={sp2}")

            time.sleep(sleep_real)

    except KeyboardInterrupt:
        print("\nSimulação interrompida pelo usuário.")
    finally:
        lab.Q1(0)
        lab.Q2(0)
        lab.close()

    # salva CSV
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # salva JSON
    with open(json_file, 'w') as f:
        json.dump(rows, f, indent=2)

    print(f"Arquivos gerados: {csv_file}, {json_file}")


if __name__ == "__main__":
    main()
