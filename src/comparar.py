"""
comparar.py - Executa as três estratégias com o MESMO conjunto de registros para
vários tamanhos de bloco e gera uma tabela comparativa (terminal + CSV).

Uso:  python comparar.py [--registros 1000] [--semente 42] [--saida ../resultados/comparacao.csv]
"""

import argparse
import csv
import os

import armazenamento as arm
import estatisticas as est
from gerador import gerar_alunos

TAMANHOS = (256, 512, 1024, 2048, 4096)


def comparar(alunos, tamanhos=TAMANHOS):
    linhas = []
    for tam in tamanhos:
        for modo in arm.MODOS:
            try:
                blocos = arm.empacotar(modo, alunos, tam)
            except arm.ErroArmazenamento:
                continue
            e = est.calcular(blocos, tam, len(alunos))
            linhas.append({
                "bloco": tam, "modo": modo, "blocos": e.total_blocos,
                "ocupacao_media_pct": round(e.ocupacao_media, 2),
                "blocos_cheios": e.blocos_cheios, "blocos_parciais": e.blocos_parciais,
                "bytes_arquivo": e.capacidade,
                "eficiencia_pct": round(e.eficiencia, 2),
            })
    return linhas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registros", type=int, default=1000)
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--saida", default="../resultados/comparacao.csv")
    args = p.parse_args()

    alunos = gerar_alunos(args.registros, args.semente)
    linhas = comparar(alunos)

    os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
    with open(args.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    print(f"{args.registros} registros, semente {args.semente}\n")
    print(f"{'Bloco':>6} {'Modo':<20} {'Blocos':>7} {'Ocup.med.':>10} {'Cheios':>7} {'Parciais':>9} {'Arquivo(B)':>11} {'Eficiencia':>11}")
    for r in linhas:
        print(f"{r['bloco']:>6} {r['modo']:<20} {r['blocos']:>7} {est.pct(r['ocupacao_media_pct']):>10} "
              f"{r['blocos_cheios']:>7} {r['blocos_parciais']:>9} {r['bytes_arquivo']:>11} {est.pct(r['eficiencia_pct']):>11}")
    print(f"\nCSV salvo em {args.saida}")


if __name__ == "__main__":
    main()
