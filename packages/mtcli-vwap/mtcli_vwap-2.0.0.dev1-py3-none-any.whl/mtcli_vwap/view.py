import click
from .conf import DIGITOS


def exibir_vwap(resultado: dict | None, symbol: str, verbose: bool = False):
    """
    Exibe o resultado da VWAP de forma acessível no terminal.

    Disposição vertical:
    - Bandas superiores (do maior desvio para o menor)
    - VWAP centralizada
    - Bandas inferiores (do menor desvio para o maior)
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

    # Ordenação correta por nível
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
