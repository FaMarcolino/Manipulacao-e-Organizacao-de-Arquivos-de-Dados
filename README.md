# TP01 – AEDS II: Manipulação e Organização de Arquivos de Dados

Simulador de armazenamento de registros de alunos em um arquivo binário `.dat` dividido em blocos de tamanho fixo,
com três estratégias: **registros fixos**, **variáveis contíguos** e **variáveis espalhados**.
Python 3, apenas biblioteca padrão.

## Estrutura

| Pasta/arquivo | Conteúdo |
|---|---|
| `src/registro.py` | campos do aluno e serialização (fixo com `#`; variável com `|`) |
| `src/gerador.py` | geração de dados fictícios (reprodutível por semente) |
| `src/armazenamento.py` | empacotamento em blocos, gravação e leitura do `.dat` |
| `src/estatisticas.py` | métricas e mapa de ocupação (com barras em texto) |
| `src/main.py` | programa principal (interativo ou por argumentos) |
| `src/comparar.py` | comparação das estratégias para vários tamanhos de bloco |
| `tests/` | 17 testes unitários |
| `dados/` | arquivos `.dat` gerados (1000 registros, bloco de 512 B) + mapas `_mapa.txt` |
| `resultados/comparacao.csv` | tabela comparativa |
| `relatorio/relatorio.pdf` | relatório descritivo (decisões de projeto, resultados, análise) |
| `relatorio/relatorio.docx` | o mesmo relatório em Word (editável; gerado por `preparar_docx.py` + `gerar_docx.js`) |

## Como executar

```bash
cd src
python main.py                       # interativo: pergunta nº de registros, bloco, modo e espalhamento
python main.py --registros 1000 --bloco 512 --modo fixo --saida ../dados/alunos_fixo.dat
python main.py --registros 1000 --bloco 512 --modo variavel --espalhamento nao --saida ../dados/alunos_variavel_contiguo.dat
python main.py --registros 1000 --bloco 512 --modo variavel --espalhamento sim --saida ../dados/alunos_variavel_espalhado.dat
python main.py ... --mapa completo   # mostra o mapa de todos os blocos no terminal
python comparar.py                   # tabela comparativa
cd ..
python -m unittest discover -s tests -v
```

Para regenerar o relatório: `cd relatorio && python gerar_relatorio.py` (usa Edge ou Chrome para criar o PDF).

## Resultados (1000 registros, bloco de 512 bytes)

| Estratégia | Blocos | Ocupação média | Eficiência (dados úteis) |
|---|---|---|---|
| Fixo (169 B/registro) | 334 | 98,8% | 61,5% |
| Variável contíguo | 251 | 89,7% | 81,9% |
| Variável espalhado | 227 | 99,7% | 90,5% |
