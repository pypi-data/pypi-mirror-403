"""
Configurações padrão do plugin mtcli-vwap.

Este módulo centraliza os valores de configuração utilizados pela CLI e
pelos demais componentes do plugin (controller, model e view).

As configurações seguem a seguinte ordem de prioridade:
1. Variáveis de ambiente
2. Arquivo de configuração do mtcli
3. Valores padrão (fallback)

Este módulo NÃO contém lógica de cálculo nem regras de negócio.
Seu único objetivo é fornecer parâmetros de configuração padronizados.
"""

import os
from mtcli.conf import config

# ----------------------------------------------------------------------
# Parâmetros principais do cálculo
# ----------------------------------------------------------------------

# Código do ativo (ex: WIN$N, WDO$N, PETR4)
SYMBOL = os.getenv(
    "SYMBOL",
    config["DEFAULT"].get("symbol", fallback="WIN$N"),
)

# Timeframe em minutos utilizado no cálculo da VWAP
MINUTES = int(
    os.getenv(
        "MINUTES",
        config["DEFAULT"].getint("minutes", fallback=1),
    )
)

# Número máximo de candles carregados do MT5
LIMIT = int(
    os.getenv(
        "LIMIT",
        config["DEFAULT"].getint("limit", fallback=0),
    )
)

# Tipo padrão de ancoragem da VWAP
# Valores esperados: abertura, ajuste, hora, maxima, minima
ANCHOR = os.getenv(
    "ANCHOR",
    config["DEFAULT"].get("anchor", fallback="abertura"),
)

# Quantidade padrão de bandas de desvio padrão
BANDS = int(
    os.getenv(
        "BANDS",
        config["DEFAULT"].getint("bands", fallback=0),
    )
)

# ----------------------------------------------------------------------
# Parâmetros de exibição
# ----------------------------------------------------------------------

# Número de casas decimais exibidas na saída textual
DIGITOS = int(
    os.getenv(
        "DIGITOS",
        config["DEFAULT"].getint("digitos", fallback=0),
    )
)
