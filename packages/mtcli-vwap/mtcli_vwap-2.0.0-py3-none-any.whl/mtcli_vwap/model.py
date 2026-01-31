"""
Módulo de cálculo da VWAP (Volume Weighted Average Price) para uso com MetaTrader 5.

Este módulo suporta:
- VWAP ancorada na abertura do pregão
- VWAP ancorada por horário específico
- VWAP ancorada na máxima ou mínima do período
- Bandas de desvio padrão ponderadas por volume (modelo profissional)

Indicado para uso em análise intraday de índice e dólar,
em conjunto com Volume Profile, tape reading e price action.
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from mtcli.mt5_context import mt5_conexao
from mtcli.logger import setup_logger

log = setup_logger()


def calcular_vwap(
    symbol: str,
    minutes: int,
    limit: int,
    anchor_type: str = "abertura",
    anchor_time: datetime | None = None,
    bandas: int = 0,
):
    """
    Calcula a VWAP (Volume Weighted Average Price) a partir dos dados do MT5.

    :param symbol: Ativo (ex: WIN$, WDO$, WING26)
    :param minutes: Timeframe em minutos
    :param limit: Quantidade de candles
    :param anchor_type: Tipo de ancoragem
        - "abertura": início do pregão
        - "hora": horário específico
        - "maxima": a partir da máxima do período
        - "minima": a partir da mínima do período
    :param anchor_time: datetime usado quando anchor_type="hora"
    :param bandas: Quantidade de bandas de desvio padrão
    :return: dict com resultado estruturado ou None
    """
    with mt5_conexao():
        if not mt5.symbol_select(symbol, True):
            log.error(f"Erro ao selecionar símbolo {symbol}")
            return None

        timeframe = _get_timeframe(minutes)
        utc_from = datetime.now() - timedelta(minutes=limit * minutes)
        rates = mt5.copy_rates_from(symbol, timeframe, utc_from, limit)

        if rates is None or len(rates) == 0:
            log.warning(f"Sem dados para VWAP {symbol}")
            return None

    df = pd.DataFrame(rates)
    df["datetime"] = pd.to_datetime(df["time"], unit="s")

    # =========================
    # ANCORAGEM
    # =========================
    if anchor_type == "abertura":
        data_pregao = df["datetime"].dt.date.max()
        df = df[df["datetime"].dt.date == data_pregao]

    elif anchor_type == "hora" and anchor_time:
        df = df[df["datetime"] >= anchor_time]

    elif anchor_type == "maxima":
        idx = df["high"].idxmax()
        df = df.loc[idx:]

    elif anchor_type == "minima":
        idx = df["low"].idxmin()
        df = df.loc[idx:]

    if df.empty:
        log.warning("DataFrame vazio após ancoragem")
        return None

    # =========================
    # CÁLCULO DA VWAP
    # =========================
    df["tp"] = (df["high"] + df["low"] + df["close"]) / 3
    df["pv"] = df["tp"] * df["real_volume"]

    volume_acumulado = df["real_volume"].cumsum()
    pv_acumulado = df["pv"].cumsum()

    df["vwap"] = pv_acumulado / volume_acumulado

    vwap_final = float(df["vwap"].iloc[-1])

    resultado = {
        "vwap": vwap_final,
        "anchor_type": anchor_type,
        "anchor_time": anchor_time.isoformat() if anchor_time else None,
    }

    # =========================
    # BANDAS POR DESVIO DE VOLUME
    # =========================
    if bandas > 0:
        df["desvio_vol"] = ((df["tp"] - df["vwap"]) ** 2) * df["real_volume"]
        variancia = df["desvio_vol"].sum() / volume_acumulado.iloc[-1]
        std_vwap = variancia ** 0.5

        for i in range(1, bandas + 1):
            resultado[f"banda_sup_{i}"] = vwap_final + i * std_vwap
            resultado[f"banda_inf_{i}"] = vwap_final - i * std_vwap

    return resultado


def _get_timeframe(minutes: int):
    """Converte minutos para timeframe do MetaTrader 5."""
    return {
        1: mt5.TIMEFRAME_M1,
        2: mt5.TIMEFRAME_M2,
        3: mt5.TIMEFRAME_M3,
        5: mt5.TIMEFRAME_M5,
        10: mt5.TIMEFRAME_M10,
        15: mt5.TIMEFRAME_M15,
        30: mt5.TIMEFRAME_M30,
        60: mt5.TIMEFRAME_H1,
        120: mt5.TIMEFRAME_H2,
        240: mt5.TIMEFRAME_H4,
    }.get(minutes, mt5.TIMEFRAME_M1)
