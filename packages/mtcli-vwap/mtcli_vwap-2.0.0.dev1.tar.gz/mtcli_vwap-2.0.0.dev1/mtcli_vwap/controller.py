from datetime import datetime
from .model import calcular_vwap


def obter_vwap(
    symbol: str,
    minutes: int,
    limit: int,
    anchor_type: str = "abertura",
    anchor_time: datetime | None = None,
    bandas: int = 0,
):
    """
    Orquestra o cálculo da VWAP delegando a lógica ao model.

    :return: dicionário com VWAP, bandas e metadados ou None
    """
    return calcular_vwap(
        symbol=symbol,
        minutes=minutes,
        limit=limit,
        anchor_type=anchor_type,
        anchor_time=anchor_time,
        bandas=bandas,
    )

