"""
estatisticas.py - Cálculo das estatísticas de uso dos blocos e impressão do
mapa de ocupação (com gráfico de barras em texto).

Definições
----------
* bytes ocupados  : bytes realmente gravados em um bloco (registros + cabeçalhos
                    + preenchimento '#' dos campos fixos), sem o padding final.
* ocupação média  : média dos percentuais (ocupados / B) de todos os blocos.
* eficiência      : bytes de DADOS ÚTEIS (conteúdo dos campos) / capacidade total
                    (nº de blocos * B). Preenchimento '#', separadores,
                    cabeçalhos e sobra no fim dos blocos NÃO contam como útil.
"""

from dataclasses import dataclass


@dataclass
class Estatisticas:
    tam_bloco: int
    total_registros: int
    total_blocos: int
    capacidade: int            # total_blocos * tam_bloco
    bytes_ocupados: int
    bytes_uteis: int
    ocupacao_media: float      # 0..100
    blocos_cheios: int         # blocos com 100% de ocupação
    blocos_parciais: int       # blocos com ocupação < 100%
    registros_por_bloco: float
    eficiencia: float          # 0..100 (dados úteis / capacidade)


def calcular(blocos: list, tam_bloco: int, total_registros: int) -> Estatisticas:
    n = len(blocos)
    ocupados = sum(b.ocupados for b in blocos)
    uteis = sum(b.uteis for b in blocos)
    capacidade = n * tam_bloco
    cheios = sum(1 for b in blocos if b.ocupados == tam_bloco)
    return Estatisticas(
        tam_bloco=tam_bloco,
        total_registros=total_registros,
        total_blocos=n,
        capacidade=capacidade,
        bytes_ocupados=ocupados,
        bytes_uteis=uteis,
        ocupacao_media=sum(100.0 * b.ocupados / tam_bloco for b in blocos) / n,
        blocos_cheios=cheios,
        blocos_parciais=n - cheios,
        registros_por_bloco=total_registros / n,
        eficiencia=100.0 * uteis / capacidade,
    )


def pct(valor: float) -> str:
    """Formata percentual com vírgula decimal (ex.: 78,6%)."""
    return f"{valor:.1f}".replace(".", ",") + "%"


def linhas_mapa(blocos: list, tam_bloco: int, largura_barra: int = 30) -> list:
    """Uma linha por bloco: bytes, percentual, barra de ocupação e detalhes."""
    w = len(str(len(blocos)))
    linhas = []
    for i, b in enumerate(blocos, start=1):
        p = 100.0 * b.ocupados / tam_bloco
        cheio = round(largura_barra * b.ocupados / tam_bloco)
        if b.ocupados < tam_bloco:
            cheio = min(cheio, largura_barra - 1)  # barra só fica cheia se o bloco estiver cheio
        barra = "#" * cheio + "." * (largura_barra - cheio)
        detalhe = f"{b.registros} reg."
        if b.herda_fragmento:
            detalhe += " [<- continuacao]"
        if b.deixa_fragmento:
            detalhe += " [fragmento ->]"
        linhas.append(
            f"Bloco {i:>{w}}: {b.ocupados:>5} bytes ({pct(p):>6} cheio) |{barra}| {detalhe}"
        )
    return linhas


def resumo(e: Estatisticas, modo: str) -> list:
    return [
        f"Modo de armazenamento      : {modo}",
        f"Tamanho do bloco           : {e.tam_bloco} bytes",
        f"Registros armazenados      : {e.total_registros}",
        f"Total de blocos utilizados : {e.total_blocos}",
        f"Registros por bloco (media): {str(round(e.registros_por_bloco, 2)).replace('.', ',')}",
        f"Ocupacao media dos blocos  : {pct(e.ocupacao_media)}",
        f"Blocos 100% cheios         : {e.blocos_cheios}",
        f"Blocos parcialmente usados : {e.blocos_parciais}",
        f"Bytes gravados / capacidade: {e.bytes_ocupados} / {e.capacidade}",
        f"Bytes de dados uteis       : {e.bytes_uteis}",
        f"Eficiencia de armazenamento: {pct(e.eficiencia)}  (dados uteis / capacidade)",
    ]
