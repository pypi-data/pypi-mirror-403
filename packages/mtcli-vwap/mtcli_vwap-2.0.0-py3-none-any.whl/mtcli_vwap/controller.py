"""
Controller da VWAP (Volume Weighted Average Price).

Este módulo atua como camada intermediária entre a interface de linha
de comando (CLI / View) e o modelo de cálculo (model).

Responsabilidades:
- Orquestrar chamadas ao cálculo da VWAP
- Encaminhar corretamente os parâmetros de ancoragem e bandas
- Retornar dados estruturados (dict / JSON-friendly)
- Manter separação clara entre regra de negócio e apresentação

Este controller não executa cálculos nem formatação de saída.
"""

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
    Orquestra o cálculo da VWAP delegando a lógica ao módulo model.

    Esta função serve como ponto único de acesso ao cálculo da VWAP
    para a camada de apresentação (CLI/View) ou para outros plugins
    que desejem consumir VWAP e bandas de forma estruturada.

    Tipos de ancoragem suportados:
    - "abertura": início do pregão
    - "hora": horário específico (requer anchor_time)
    - "maxima": a partir da máxima do período analisado
    - "minima": a partir da mínima do período analisado

    :param symbol: Ativo negociado (ex: WIN$, WDO$, WING26)
    :param minutes: Timeframe em minutos
    :param limit: Quantidade de candles analisados
    :param anchor_type: Tipo de ancoragem da VWAP
    :param anchor_time: Horário específico usado quando anchor_type="hora"
    :param bandas: Quantidade de bandas de desvio padrão ponderadas por volume
    :return: Dicionário com VWAP, bandas e metadados ou None em caso de erro
    """
    return calcular_vwap(
        symbol=symbol,
        minutes=minutes,
        limit=limit,
        anchor_type=anchor_type,
        anchor_time=anchor_time,
        bandas=bandas,
    )
