import os
from mtcli.conf import config

"""
Configurações padrão do plugin mtcli-vwap.
Valores podem ser sobrescritos por variáveis de ambiente
ou pelo arquivo de configuração do mtcli.
"""

SYMBOL = os.getenv("SYMBOL", config["DEFAULT"].get("symbol", fallback="WIN$N"))
MINUTES = int(os.getenv("MINUTES", config["DEFAULT"].getint("minutes", fallback=1)))
LIMIT = int(os.getenv("LIMIT", config["DEFAULT"].getint("limit", fallback=0)))
ANCHOR = os.getenv("ANCHOR", config["DEFAULT"].get("anchor", fallback="abertura"))
BANDS = int(os.getenv("BANDS", config["DEFAULT"].getint("bands", fallback=0)))

# Número de casas decimais exibidas
DIGITOS = int(os.getenv("DIGITOS", config["DEFAULT"].getint("digitos", fallback=0)))

