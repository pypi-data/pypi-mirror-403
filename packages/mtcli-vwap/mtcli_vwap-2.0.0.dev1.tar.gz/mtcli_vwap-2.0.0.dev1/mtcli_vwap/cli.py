import json
from datetime import datetime
import click

from .controller import obter_vwap
from .view import exibir_vwap
from .conf import SYMBOL, MINUTES, LIMIT, ANCHOR, BANDS


@click.command()
@click.version_option(package_name="mtcli-vwap")
@click.option("--symbol", "-s", default=SYMBOL, show_default=True, help="Código do ativo.")
@click.option(
    "--minutes",
    "-m",
    default=MINUTES,
    show_default=True,
    help="Timeframe em minutos usado no cálculo da VWAP.",
)
@click.option(
    "--limit",
    "-l",
    default=LIMIT,
    show_default=True,
    help="Número de candles utilizados.",
)
@click.option(
    "--anchor",
    "-a",
    type=click.Choice(["abertura", "ajuste", "hora"]),
    default=ANCHOR,
    show_default=True,
    help="Tipo de ancoragem da VWAP.",
)
@click.option(
    "--anchor-time",
    "-at",
    default=None,
    help="Horário de ancoragem (YYYY-MM-DD HH:MM). Usado com anchor=hora.",
)
@click.option(
    "--bands",
    "-b",
    default=BANDS,
    show_default=True,
    help="Número de bandas de desvio padrão.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Retorna o resultado em JSON.",
)
@click.option(
    "--verbose",
    "-vv",
    is_flag=True,
    default=False,
    show_default=True,
    help="Modo verboso.",
)
def vwap(symbol: str, minutes: int, limit: int, anchor: str, anchor_time: str | None, bands: int, json_output: bool, verbose: bool):
    """
    Calcula a VWAP (Volume Weighted Average Price) do ativo no intraday.

    Suporta VWAP ancorada (abertura, ajuste ou horário específico),
    bandas de desvio padrão e saída em JSON para integração com outros plugins.
    """
    anchor_dt = None
    if anchor == "hora" and anchor_time:
        anchor_dt = datetime.strptime(anchor_time, "%Y-%m-%d %H:%M")

    resultado = obter_vwap(
        symbol=symbol,
        minutes=minutes,
        limit=limit,
        anchor_type=anchor,
        anchor_time=anchor_dt,
        bandas=bands,
    )

    if json_output:
        click.echo(json.dumps(resultado, ensure_ascii=False))
    else:
        exibir_vwap(resultado, symbol, verbose)

