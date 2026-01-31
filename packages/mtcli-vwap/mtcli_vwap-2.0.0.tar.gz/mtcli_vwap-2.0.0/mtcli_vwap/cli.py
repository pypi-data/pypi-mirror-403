"""
Interface de linha de comando (CLI) do plugin mtcli-vwap.

Este módulo define o comando `vwap` integrado ao mtcli, sendo responsável por:

- Interpretar argumentos e opções da linha de comando
- Validar e converter parâmetros de entrada (ex: datas e horários)
- Orquestrar a chamada ao controller
- Direcionar a saída para modo humano (view) ou JSON (automação)

Este módulo NÃO realiza cálculos de VWAP nem lógica de negócio.
Toda a responsabilidade de cálculo é delegada ao controller/model.
"""

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
    help="Horário de ancoragem (YYYY-MM-DD HH:MM). Usado apenas com anchor=hora.",
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
    help="Retorna o resultado em JSON para uso por outros plugins ou scripts.",
)
@click.option(
    "--verbose",
    "-vv",
    is_flag=True,
    default=False,
    show_default=True,
    help="Modo verboso (reservado para expansões futuras).",
)
def vwap(
    symbol: str,
    minutes: int,
    limit: int,
    anchor: str,
    anchor_time: str | None,
    bands: int,
    json_output: bool,
    verbose: bool,
):
    """
    Executa o cálculo da VWAP (Volume Weighted Average Price) no intraday.

    Suporta:
    - VWAP ancorada por abertura, ajuste ou horário específico
    - Bandas de desvio padrão
    - Saída textual acessível ou JSON estruturado

    Este comando pode ser utilizado tanto para análise manual no terminal
    quanto como fonte de dados para automações e outros plugins do mtcli.

    :param symbol: Código do ativo
    :param minutes: Timeframe em minutos
    :param limit: Quantidade de candles utilizados
    :param anchor: Tipo de ancoragem da VWAP
    :param anchor_time: Horário específico de ancoragem (quando aplicável)
    :param bands: Número de bandas de desvio padrão
    :param json_output: Define se a saída será em JSON
    :param verbose: Ativa modo verboso (não afeta o cálculo)
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
