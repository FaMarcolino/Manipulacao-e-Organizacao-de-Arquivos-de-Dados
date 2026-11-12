"""
gerador.py - Geração de registros fictícios de alunos (somente biblioteca padrão).

Os dados são gerados de forma reprodutível a partir de uma semente (seed), de
modo que o mesmo conjunto de registros possa ser usado para comparar as
estratégias de armazenamento.
"""

import random

from registro import Aluno, CAMPOS, validar

LARGURA = dict(CAMPOS)

NOMES_FEM = [
    "Ana", "Maria", "Beatriz", "Camila", "Daniela", "Eduarda", "Fernanda", "Gabriela",
    "Helena", "Isabela", "Juliana", "Larissa", "Mariana", "Natalia", "Patricia",
    "Rafaela", "Sabrina", "Tatiana", "Vanessa", "Luiza", "Aline", "Bruna", "Carolina",
    "Débora", "Elisa", "Flavia", "Giovana", "Heloisa", "Ingrid", "Jessica",
    "Maria Aparecida", "Maria das Gracas", "Ana Paula", "Maria Eduarda",
]
NOMES_MASC = [
    "Joao", "Pedro", "Lucas", "Gabriel", "Rafael", "Matheus", "Felipe", "Bruno",
    "Carlos", "Daniel", "Eduardo", "Fernando", "Gustavo", "Henrique", "Igor",
    "Jose", "Leonardo", "Marcelo", "Nicolas", "Otavio", "Paulo", "Ricardo",
    "Samuel", "Thiago", "Vinicius", "Antonio", "Alexandre", "Diego", "Rodrigo",
    "Jose Carlos", "Luiz Fernando", "Joao Pedro", "Carlos Eduardo",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento",
    "Andrade", "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas",
    "Cardoso", "Ramos", "Goncalves", "Santana", "Teixeira", "Albuquerque",
    "Vasconcelos", "Guimaraes", "Figueiredo", "Albuquerque Filho", "Cavalcanti",
]
CURSOS = [
    "Ciencia da Computacao", "Engenharia de Computacao", "Sistemas de Informacao",
    "Engenharia Civil", "Engenharia Eletrica", "Engenharia Mecanica",
    "Engenharia de Producao", "Engenharia Quimica", "Medicina", "Direito",
    "Administracao", "Ciencias Contabeis", "Psicologia", "Arquitetura e Urbanismo",
    "Matematica", "Fisica", "Quimica", "Biologia", "Letras", "Historia",
    "Geografia", "Pedagogia", "Enfermagem", "Farmacia", "Odontologia",
    "Engenharia Ambiental", "Engenharia de Controle e Automacao", "Economia",
    "Estatistica", "Jornalismo",
]


def _sem_acento(texto: str) -> str:
    tabela = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
                           "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")
    return texto.translate(tabela)


def _ajustar(nome: str, limite: int) -> str:
    """Remove sobrenomes do final até o nome caber no limite do campo."""
    palavras = nome.split()
    while len(" ".join(palavras)) > limite and len(palavras) > 1:
        palavras.pop()
    return " ".join(palavras)[:limite].strip()


def _cpf(rnd: random.Random) -> str:
    """CPF com dígitos verificadores válidos (11 dígitos, sem pontuação)."""
    while True:
        base = [rnd.randint(0, 9) for _ in range(9)]
        if len(set(base)) > 1:  # evita sequências do tipo 111.111.111
            break
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(base))
        resto = (soma * 10) % 11
        base.append(0 if resto == 10 else resto)
    return "".join(map(str, base))


def gerar_alunos(quantidade: int, semente: int = 42) -> list:
    """Gera `quantidade` alunos com matrículas únicas e campos de tamanho variado."""
    rnd = random.Random(semente)
    matriculas = set()
    alunos = []
    while len(alunos) < quantidade:
        ano = rnd.randint(2008, 2025)
        matricula = ano * 100000 + rnd.randint(0, 99999)  # 9 dígitos
        if matricula in matriculas:
            continue
        matriculas.add(matricula)

        sobrenome_pai = rnd.choice(SOBRENOMES)
        sobrenome_mae = rnd.choice(SOBRENOMES)
        # Alguns alunos têm dois nomes próprios e/ou sobrenome composto.
        nome_aluno = rnd.choice(NOMES_FEM if rnd.random() < 0.5 else NOMES_MASC)
        if rnd.random() < 0.3:
            nome_aluno += " " + rnd.choice(NOMES_FEM + NOMES_MASC)
        extra = " " + rnd.choice(SOBRENOMES) if rnd.random() < 0.25 else ""
        nome = nome_aluno + extra + " " + sobrenome_mae + " " + sobrenome_pai

        mae = rnd.choice(NOMES_FEM) + " " + sobrenome_mae + (" " + rnd.choice(SOBRENOMES) if rnd.random() < 0.3 else "")
        pai = rnd.choice(NOMES_MASC) + " " + sobrenome_pai + (" " + rnd.choice(SOBRENOMES) if rnd.random() < 0.3 else "")

        # CA entre 0,00 e 10,00, concentrado em torno de 7 (distribuição normal truncada).
        ca = round(min(10.0, max(0.0, rnd.gauss(7.0, 1.5))), 2)

        aluno = Aluno(
            matricula=matricula,
            nome=_ajustar(_sem_acento(nome), LARGURA["nome"]),
            cpf=_cpf(rnd),
            curso=_ajustar(_sem_acento(rnd.choice(CURSOS)), LARGURA["curso"]),
            mae=_ajustar(_sem_acento(mae), LARGURA["mae"]),
            pai=_ajustar(_sem_acento(pai), LARGURA["pai"]),
            ano_ingresso=ano,
            ca=ca,
        )
        validar(aluno)
        alunos.append(aluno)
    return alunos
