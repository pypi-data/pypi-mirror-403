"""
Configurações padrão do plugin mtcli-volume.

Os valores podem ser sobrescritos por:
- Variáveis de ambiente
- Arquivo de configuração do mtcli

Este módulo não contém lógica, apenas parâmetros padrão.
"""

import os
from mtcli.conf import config

SYMBOL = os.getenv("SYMBOL", config["DEFAULT"].get("symbol", fallback="WIN$N"))
DIGITOS = int(os.getenv("DIGITOS", config["DEFAULT"].getint("digitos", fallback=0)))
PERIOD = os.getenv("PERIOD", config["DEFAULT"].get("period", fallback="M1"))
LIMIT = int(os.getenv("LIMIT", config["DEFAULT"].getint("limit", fallback=566)))
RANGE = float(os.getenv("RANGE", config["DEFAULT"].getfloat("range", fallback=100)))
VOLUME = os.getenv("VOLUME", config["DEFAULT"].get("volume", fallback="tick"))
INICIO = os.getenv("INICIO", config["DEFAULT"].get("inicio", fallback=""))
FIM = os.getenv("FIM", config["DEFAULT"].get("fim", fallback=""))
TIMEZONE = os.getenv("TIMEZONE", config["DEFAULT"].get("timezone", fallback="America/Sao_Paulo"))
FORMAT = os.getenv("FORMAT", config["DEFAULT"].get("format", fallback="k"))
