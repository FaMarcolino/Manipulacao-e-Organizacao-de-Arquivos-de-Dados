"""
registro.py - Definição do registro de aluno e sua serialização em bytes.

Dois formatos de serialização são oferecidos:

* FIXO: cada campo ocupa uma largura constante, completada com o caractere de
  preenchimento '#'. Todo registro tem exatamente TAMANHO_FIXO bytes.
* VARIÁVEL: os campos são gravados sem preenchimento, separados por '|'.
  O tamanho do registro depende do conteúdo real dos campos.

Todos os textos são ASCII (1 caractere = 1 byte), o que permite medir o tamanho
dos registros diretamente pelo número de caracteres.
"""

from dataclasses import dataclass

PREENCHIMENTO = b"#"   # caractere de preenchimento do formato fixo
SEPARADOR = b"|"       # separador de campos do formato variável

# (nome do campo, largura máxima em bytes) - na ordem em que são gravados.
# CA é gravado como texto "d.dd" (valores de 0,00 a 10,00 => até 5 bytes).
CAMPOS = [
    ("matricula", 9),
    ("nome", 50),
    ("cpf", 11),
    ("curso", 30),
    ("mae", 30),
    ("pai", 30),
    ("ano_ingresso", 4),
    ("ca", 5),
]

LARGURAS = [largura for _, largura in CAMPOS]
TAMANHO_FIXO = sum(LARGURAS)  # 169 bytes: maior tamanho possível de um registro


@dataclass(frozen=True)
class Aluno:
    matricula: int      # 9 dígitos
    nome: str           # até 50 caracteres
    cpf: str            # 11 caracteres
    curso: str          # até 30 caracteres
    mae: str            # até 30 caracteres
    pai: str            # até 30 caracteres
    ano_ingresso: int   # 4 dígitos
    ca: float           # 0,00 a 10,00 (2 casas decimais)


def _valores_texto(a: Aluno) -> list:
    """Converte os campos do aluno para texto, já no formato de gravação."""
    return [
        f"{a.matricula:09d}",
        a.nome,
        a.cpf,
        a.curso,
        a.mae,
        a.pai,
        f"{a.ano_ingresso:04d}",
        f"{a.ca:.2f}",
    ]


def validar(a: Aluno) -> None:
    """Garante que o aluno respeita os limites de cada campo."""
    for (nome_campo, largura), valor in zip(CAMPOS, _valores_texto(a)):
        if not valor.isascii():
            raise ValueError(f"campo '{nome_campo}' contém caractere não ASCII: {valor!r}")
        if len(valor) > largura:
            raise ValueError(f"campo '{nome_campo}' excede {largura} bytes: {valor!r}")
        if SEPARADOR.decode() in valor or PREENCHIMENTO.decode() in valor:
            raise ValueError(f"campo '{nome_campo}' contém caractere reservado: {valor!r}")
    if len(a.cpf) != 11:
        raise ValueError(f"CPF deve ter 11 caracteres: {a.cpf!r}")


def bytes_uteis(a: Aluno) -> int:
    """Bytes de dados reais do aluno (conteúdo dos campos, sem preenchimento,
    separadores ou cabeçalhos). Usado na eficiência de armazenamento."""
    return sum(len(v) for v in _valores_texto(a))


# --------------------------------------------------------------------------- #
# Formato fixo
# --------------------------------------------------------------------------- #
def serializar_fixo(a: Aluno) -> bytes:
    """Registro de TAMANHO_FIXO bytes, campos completados com '#'."""
    partes = [
        v.encode("ascii").ljust(largura, PREENCHIMENTO)
        for v, largura in zip(_valores_texto(a), LARGURAS)
    ]
    return b"".join(partes)


def desserializar_fixo(dados: bytes) -> Aluno:
    if len(dados) != TAMANHO_FIXO:
        raise ValueError(f"registro fixo deve ter {TAMANHO_FIXO} bytes, recebeu {len(dados)}")
    campos, pos = [], 0
    for largura in LARGURAS:
        campos.append(dados[pos:pos + largura].rstrip(PREENCHIMENTO).decode("ascii"))
        pos += largura
    return _montar(campos)


# --------------------------------------------------------------------------- #
# Formato variável
# --------------------------------------------------------------------------- #
def serializar_variavel(a: Aluno) -> bytes:
    """Corpo do registro variável: campos separados por '|', sem preenchimento."""
    return SEPARADOR.join(v.encode("ascii") for v in _valores_texto(a))


def desserializar_variavel(corpo: bytes) -> Aluno:
    campos = corpo.decode("ascii").split(SEPARADOR.decode())
    if len(campos) != len(CAMPOS):
        raise ValueError(f"registro variável com {len(campos)} campos (esperado {len(CAMPOS)})")
    return _montar(campos)


def _montar(campos: list) -> Aluno:
    return Aluno(
        matricula=int(campos[0]),
        nome=campos[1],
        cpf=campos[2],
        curso=campos[3],
        mae=campos[4],
        pai=campos[5],
        ano_ingresso=int(campos[6]),
        ca=float(campos[7]),
    )
