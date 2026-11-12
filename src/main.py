"""
main.py - Simulador de armazenamento de registros de alunos em blocos (.DAT).

Uso interativo:
    python main.py

Uso por linha de comando (qualquer parâmetro omitido é perguntado):
    python main.py --registros 1000 --bloco 512 --modo variavel --espalhamento sim
    python main.py --registros 1000 --bloco 512 --modo fixo --saida ../dados/alunos_fixo.dat
"""

import argparse
import os
import sys

import armazenamento as arm
import estatisticas as est
from gerador import gerar_alunos
from registro import TAMANHO_FIXO


# --------------------------------------------------------------------------- #
# Entrada de dados do usuário
# --------------------------------------------------------------------------- #
def pedir_inteiro(mensagem: str, minimo: int, padrao: int = None) -> int:
    while True:
        sufixo = f" [{padrao}]" if padrao is not None else ""
        texto = input(f"{mensagem}{sufixo}: ").strip()
        if not texto and padrao is not None:
            return padrao
        if texto.isdigit() and int(texto) >= minimo:
            return int(texto)
        print(f"  Valor inválido: informe um inteiro >= {minimo}.")


def pedir_opcao(mensagem: str, opcoes: dict) -> str:
    """opcoes: {'1': ('descrição', valor), ...}. Retorna o valor escolhido."""
    print(mensagem)
    for chave, (descricao, _) in opcoes.items():
        print(f"  {chave}) {descricao}")
    while True:
        escolha = input("Opção: ").strip()
        if escolha in opcoes:
            return opcoes[escolha][1]
        print("  Opção inválida.")


def interpretar_modo(args, interativo: bool) -> str:
    """Converte as respostas (modo / espalhamento) em um dos MODOS."""
    modo = args.modo
    if modo is None:
        modo = pedir_opcao("\nModo de armazenamento:", {
            "1": ("Registros de tamanho fixo", "fixo"),
            "2": ("Registros de tamanho variável", "variavel"),
        })
    if modo == "fixo":
        return arm.FIXO
    espalhamento = args.espalhamento
    if espalhamento is None:
        espalhamento = pedir_opcao("\nRegistros variáveis:", {
            "1": ("Contíguos (sem espalhamento)", "nao"),
            "2": ("Espalhados (fragmentados entre blocos)", "sim"),
        })
    return arm.VARIAVEL_ESPALHADO if espalhamento == "sim" else arm.VARIAVEL_CONTIGUO


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #
def simular(alunos, modo, tam_bloco, caminho_dat, mostrar_mapa="resumido", salvar_mapa=True):
    """Empacota, grava, relê para verificar e imprime as estatísticas."""
    blocos = arm.empacotar(modo, alunos, tam_bloco)
    os.makedirs(os.path.dirname(os.path.abspath(caminho_dat)), exist_ok=True)
    arm.gravar(blocos, tam_bloco, caminho_dat)

    # Verificação: o arquivo gravado deve reproduzir exatamente os registros originais.
    relidos = arm.ler(caminho_dat, tam_bloco, modo)
    ok = relidos == alunos
    tamanho_arquivo = os.path.getsize(caminho_dat)
    assert tamanho_arquivo == len(blocos) * tam_bloco

    e = est.calcular(blocos, tam_bloco, len(alunos))
    mapa = est.linhas_mapa(blocos, tam_bloco)

    print("\n" + "=" * 78)
    print("RESULTADO DO ARMAZENAMENTO")
    print("=" * 78)
    print(f"Arquivo gerado             : {caminho_dat} ({tamanho_arquivo} bytes)")
    print(f"Verificacao (leitura .dat) : {'OK - registros idênticos aos originais' if ok else 'FALHOU'}")
    for linha in est.resumo(e, modo):
        print(linha)

    print("\nMAPA DE OCUPACAO DOS BLOCOS")
    print("-" * 78)
    if mostrar_mapa == "completo" or len(mapa) <= 25:
        exibidas = mapa
    else:
        exibidas = mapa[:15] + [f"   ... ({len(mapa) - 20} blocos omitidos; use --mapa completo) ..."] + mapa[-5:]
    print("\n".join(exibidas))

    if salvar_mapa:
        caminho_mapa = os.path.splitext(caminho_dat)[0] + "_mapa.txt"
        with open(caminho_mapa, "w", encoding="utf-8") as f:
            f.write("\n".join(est.resumo(e, modo)) + "\n\n")
            f.write("MAPA DE OCUPACAO DOS BLOCOS\n" + "-" * 78 + "\n")
            f.write("\n".join(mapa) + "\n")
        print(f"\nMapa completo salvo em     : {caminho_mapa}")
    return ok, e


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Simulador de armazenamento de registros em blocos (.DAT)")
    p.add_argument("--registros", type=int, help="número de registros a gerar")
    p.add_argument("--bloco", type=int, help="tamanho máximo do bloco em bytes")
    p.add_argument("--modo", choices=["fixo", "variavel"], help="tamanho dos registros")
    p.add_argument("--espalhamento", choices=["sim", "nao"], help="(modo variável) espalhar registros entre blocos")
    p.add_argument("--saida", default="alunos.dat", help="arquivo .dat de saída (padrão: alunos.dat)")
    p.add_argument("--semente", type=int, default=42, help="semente do gerador de dados (padrão: 42)")
    p.add_argument("--mapa", choices=["resumido", "completo"], default="resumido",
                   help="quantidade de linhas do mapa exibido no terminal")
    args = p.parse_args(argv)

    print("=== AEDS II - TP01: Organização de arquivos de dados em blocos ===")
    print(f"(registro de tamanho fixo = {TAMANHO_FIXO} bytes)\n")

    n = args.registros if args.registros is not None else pedir_inteiro("Número de registros a gerar", 1, 1000)
    modo = interpretar_modo(args, args.modo is None)
    alunos = gerar_alunos(n, args.semente)
    minimo = arm.tamanho_minimo_bloco(modo, alunos)

    interativo = args.bloco is None
    while True:
        tam_bloco = args.bloco if args.bloco is not None else pedir_inteiro(
            f"Tamanho máximo do bloco em bytes (mínimo {minimo})", 1, 512)
        try:
            ok, _ = simular(alunos, modo, tam_bloco, args.saida, args.mapa)
            return 0 if ok else 2
        except arm.ErroArmazenamento as erro:
            print(f"\nErro: {erro}")
            if not interativo:
                return 1
            print("Informe outro tamanho de bloco.\n")


if __name__ == "__main__":
    sys.exit(main())
