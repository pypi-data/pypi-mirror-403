"""
View da VWAP (Volume Weighted Average Price).

Este módulo é responsável exclusivamente pela apresentação textual
dos resultados da VWAP no terminal, com foco em:

- Acessibilidade (leitores de tela como NVDA / JAWS)
- Clareza semântica
- Organização vertical das informações
- Compatibilidade com uso humano e automação simples

Este módulo NÃO executa cálculos nem regras de negócio.
Toda a lógica de VWAP e bandas é delegada ao controller/model.
"""

import click
from .conf import DIGITOS


def exibir_vwap(resultado: dict | None, symbol: str, verbose: bool = False):
    """
    Exibe o resultado da VWAP de forma acessível no terminal.

    A saída é organizada em disposição vertical para facilitar
    leitura sequencial por leitores de tela e interpretação humana.

    Ordem de exibição:
    - Bandas superiores (do maior desvio para o menor)
    - VWAP central
    - Bandas inferiores (do menor desvio para o maior)

    Nenhum elemento visual, gráfico ou alinhamento espacial é utilizado,
    garantindo compatibilidade com ambientes de terminal puro.

    :param resultado: Dicionário retornado pelo controller/model
    :param symbol: Código do ativo analisado
    :param verbose: Reservado para futuras expansões de detalhamento
    """
    if not resultado:
        click.echo("Não foi possível calcular a VWAP.")
        return

    vwap = resultado.get("vwap")

    bandas_sup = []
    bandas_inf = []

    for chave, valor in resultado.items():
        if chave.startswith("banda_sup"):
            bandas_sup.append((chave, valor))
        elif chave.startswith("banda_inf"):
            bandas_inf.append((chave, valor))

    # Ordenação correta por nível numérico
    bandas_sup.sort(key=lambda x: int(x[0].split("_")[-1]), reverse=True)
    bandas_inf.sort(key=lambda x: int(x[0].split("_")[-1]))

    click.echo("")

    # Bandas superiores
    for chave, valor in bandas_sup:
        click.echo(f"{chave}: {valor:.{DIGITOS}f}")

    # VWAP central
    click.echo(f"VWAP {symbol}: {vwap:.{DIGITOS}f}")

    # Bandas inferiores
    for chave, valor in bandas_inf:
        click.echo(f"{chave}: {valor:.{DIGITOS}f}")

    click.echo("")
