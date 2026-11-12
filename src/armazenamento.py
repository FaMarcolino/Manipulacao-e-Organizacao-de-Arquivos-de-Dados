"""
armazenamento.py - Organização de registros em blocos de tamanho fixo e
gravação/leitura do arquivo .DAT.

Estratégias implementadas
-------------------------
1. FIXO              : todo registro tem TAMANHO_FIXO bytes; cabem
                       floor(B / TAMANHO_FIXO) registros por bloco, sem
                       cabeçalhos. Nenhum registro cruza a fronteira do bloco.
2. VARIÁVEL CONTÍGUO : cada registro tem cabeçalho de 3 bytes + corpo de tamanho
                       real. Se não couber no espaço livre do bloco, vai
                       inteiro para o próximo bloco.
3. VARIÁVEL ESPALHADO: como o anterior, porém o registro que não cabe é
                       dividido em fragmentos; o cabeçalho de cada fragmento
                       indica se ele continua no próximo bloco / continua o
                       fragmento do bloco anterior.

Cabeçalho de registro/fragmento (3 bytes, big-endian):
    +--------+------------------+
    | flags  | tamanho do dado  |
    | 1 byte | 2 bytes (uint16) |
    +--------+------------------+
    flags: 0x00 = fim útil do bloco (padding)
           bit 0x01 = fragmento válido
           bit 0x02 = continua no próximo bloco
           bit 0x04 = continuação de fragmento do bloco anterior

    Registro completo        -> 0x01
    Primeiro fragmento       -> 0x03
    Fragmento intermediário  -> 0x07
    Último fragmento         -> 0x05

Cada bloco é gravado no arquivo com exatamente B bytes; o espaço não usado é
completado com 0x00. O arquivo final tem, portanto, (nº de blocos * B) bytes.
"""

import struct
from dataclasses import dataclass, field

from registro import (
    Aluno,
    TAMANHO_FIXO,
    bytes_uteis,
    desserializar_fixo,
    desserializar_variavel,
    serializar_fixo,
    serializar_variavel,
    SEPARADOR,
)

# Modos de armazenamento
FIXO = "fixo"
VARIAVEL_CONTIGUO = "variavel-contiguo"
VARIAVEL_ESPALHADO = "variavel-espalhado"
MODOS = (FIXO, VARIAVEL_CONTIGUO, VARIAVEL_ESPALHADO)

# Cabeçalho dos registros variáveis
FLAG_VALIDO = 0x01
FLAG_CONTINUA = 0x02       # o registro continua no próximo bloco
FLAG_CONTINUACAO = 0x04    # este fragmento continua o do bloco anterior
FORMATO_CABECALHO = ">BH"
TAM_CABECALHO = struct.calcsize(FORMATO_CABECALHO)  # 3 bytes

PADDING = b"\x00"


class ErroArmazenamento(Exception):
    """Parâmetros inválidos (ex.: bloco menor que o menor registro possível)."""


@dataclass
class Bloco:
    """Conteúdo de um bloco já montado (ainda sem o padding final)."""
    dados: bytearray = field(default_factory=bytearray)
    uteis: int = 0                 # bytes de dados reais (campos) dentro do bloco
    registros: int = 0             # registros que COMEÇAM neste bloco
    herda_fragmento: bool = False  # começa com a continuação de um registro anterior
    deixa_fragmento: bool = False  # termina com um fragmento que continua adiante

    @property
    def ocupados(self) -> int:
        return len(self.dados)


# --------------------------------------------------------------------------- #
# Tamanho mínimo de bloco para cada modo
# --------------------------------------------------------------------------- #
def tamanho_minimo_bloco(modo: str, alunos: list) -> int:
    """Menor tamanho de bloco (bytes) que permite gravar todos os registros."""
    if modo == FIXO:
        return TAMANHO_FIXO
    if modo == VARIAVEL_CONTIGUO:
        return TAM_CABECALHO + max(len(serializar_variavel(a)) for a in alunos)
    if modo == VARIAVEL_ESPALHADO:
        return TAM_CABECALHO + 1  # cabeçalho + pelo menos 1 byte de dado
    raise ErroArmazenamento(f"modo desconhecido: {modo}")


def _validar_parametros(modo: str, alunos: list, tam_bloco: int) -> None:
    if not alunos:
        raise ErroArmazenamento("não há registros para armazenar")
    if tam_bloco > 0xFFFF + TAM_CABECALHO:
        raise ErroArmazenamento("tamanho de bloco máximo suportado: 65538 bytes")
    minimo = tamanho_minimo_bloco(modo, alunos)
    if tam_bloco < minimo:
        raise ErroArmazenamento(
            f"bloco de {tam_bloco} bytes é pequeno demais para o modo '{modo}'; "
            f"o mínimo é {minimo} bytes"
        )


# --------------------------------------------------------------------------- #
# Empacotamento
# --------------------------------------------------------------------------- #
def empacotar_fixo(alunos: list, tam_bloco: int) -> list:
    """Registros de tamanho fixo: floor(B / 169) registros por bloco."""
    _validar_parametros(FIXO, alunos, tam_bloco)
    por_bloco = tam_bloco // TAMANHO_FIXO
    blocos = []
    for i, aluno in enumerate(alunos):
        if i % por_bloco == 0:
            blocos.append(Bloco())
        b = blocos[-1]
        b.dados += serializar_fixo(aluno)
        b.uteis += bytes_uteis(aluno)
        b.registros += 1
    return blocos


def empacotar_variavel_contiguo(alunos: list, tam_bloco: int) -> list:
    """Registros variáveis sem espalhamento: o que não couber vai ao próximo bloco."""
    _validar_parametros(VARIAVEL_CONTIGUO, alunos, tam_bloco)
    blocos = [Bloco()]
    for aluno in alunos:
        corpo = serializar_variavel(aluno)
        necessario = TAM_CABECALHO + len(corpo)
        if blocos[-1].ocupados + necessario > tam_bloco:
            blocos.append(Bloco())
        b = blocos[-1]
        b.dados += struct.pack(FORMATO_CABECALHO, FLAG_VALIDO, len(corpo)) + corpo
        b.uteis += bytes_uteis(aluno)
        b.registros += 1
    return blocos


def empacotar_variavel_espalhado(alunos: list, tam_bloco: int) -> list:
    """Registros variáveis com espalhamento: o registro é fragmentado entre blocos."""
    _validar_parametros(VARIAVEL_ESPALHADO, alunos, tam_bloco)
    blocos = [Bloco()]
    for aluno in alunos:
        corpo = serializar_variavel(aluno)
        pos = 0
        primeiro = True
        while pos < len(corpo):
            atual = blocos[-1]
            livre = tam_bloco - atual.ocupados
            if livre < TAM_CABECALHO + 1:
                # Sobra espaço apenas para um cabeçalho sem dados: abre novo bloco.
                blocos.append(Bloco())
                continue
            restante = len(corpo) - pos
            cabe_tudo = TAM_CABECALHO + restante <= livre
            tamanho = restante if cabe_tudo else livre - TAM_CABECALHO
            fragmento = corpo[pos:pos + tamanho]

            flags = FLAG_VALIDO
            if not cabe_tudo:
                flags |= FLAG_CONTINUA
            if not primeiro:
                flags |= FLAG_CONTINUACAO

            atual.dados += struct.pack(FORMATO_CABECALHO, flags, tamanho) + fragmento
            # Bytes úteis do fragmento = bytes que não são separadores de campo.
            atual.uteis += len(fragmento) - fragmento.count(SEPARADOR)
            if primeiro:
                atual.registros += 1
            else:
                atual.herda_fragmento = True
            if not cabe_tudo:
                atual.deixa_fragmento = True

            pos += tamanho
            primeiro = False
    return blocos


def empacotar(modo: str, alunos: list, tam_bloco: int) -> list:
    if modo == FIXO:
        return empacotar_fixo(alunos, tam_bloco)
    if modo == VARIAVEL_CONTIGUO:
        return empacotar_variavel_contiguo(alunos, tam_bloco)
    if modo == VARIAVEL_ESPALHADO:
        return empacotar_variavel_espalhado(alunos, tam_bloco)
    raise ErroArmazenamento(f"modo desconhecido: {modo}")


# --------------------------------------------------------------------------- #
# Arquivo .DAT
# --------------------------------------------------------------------------- #
def gravar(blocos: list, tam_bloco: int, caminho: str) -> None:
    """Grava os blocos sequencialmente; cada um completado com 0x00 até B bytes."""
    with open(caminho, "wb") as arq:
        for b in blocos:
            if b.ocupados > tam_bloco:
                raise ErroArmazenamento("bloco excede o tamanho máximo (erro interno)")
            arq.write(bytes(b.dados) + PADDING * (tam_bloco - b.ocupados))


def ler(caminho: str, tam_bloco: int, modo: str) -> list:
    """Lê o arquivo .DAT bloco a bloco e reconstrói a lista de alunos."""
    alunos = []
    pendente = bytearray()  # fragmentos do registro que atravessa blocos
    with open(caminho, "rb") as arq:
        while True:
            bloco = arq.read(tam_bloco)
            if not bloco:
                break
            if len(bloco) != tam_bloco:
                raise ErroArmazenamento("arquivo corrompido: último bloco incompleto")
            if modo == FIXO:
                for i in range(tam_bloco // TAMANHO_FIXO):
                    reg = bloco[i * TAMANHO_FIXO:(i + 1) * TAMANHO_FIXO]
                    if reg[0] == 0:  # espaço não usado no fim do bloco
                        break
                    alunos.append(desserializar_fixo(reg))
            else:
                pos = 0
                while pos + TAM_CABECALHO <= tam_bloco and bloco[pos] != 0:
                    flags, tamanho = struct.unpack_from(FORMATO_CABECALHO, bloco, pos)
                    pos += TAM_CABECALHO
                    dados = bloco[pos:pos + tamanho]
                    pos += tamanho
                    if flags & FLAG_CONTINUACAO:
                        if not pendente:
                            raise ErroArmazenamento("continuação sem fragmento inicial")
                        pendente += dados
                    else:
                        pendente = bytearray(dados)
                    if not flags & FLAG_CONTINUA:
                        alunos.append(desserializar_variavel(bytes(pendente)))
                        pendente = bytearray()
    if pendente:
        raise ErroArmazenamento("arquivo termina no meio de um registro")
    return alunos
