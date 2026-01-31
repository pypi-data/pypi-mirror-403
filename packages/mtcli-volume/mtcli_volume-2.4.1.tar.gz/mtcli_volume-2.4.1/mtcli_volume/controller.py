"""
Controller do plugin mtcli-volume.

Este módulo coordena o fluxo de execução do Volume Profile:
- Solicita dados históricos ao model
- Aciona o cálculo do Volume Profile
- Calcula estatísticas de Market Profile
- Prepara informações de contexto (datas, timezone, candles)

Não realiza cálculos matemáticos nem formatação de saída.
"""

from datetime import datetime, timedelta, timezone
import zoneinfo
import numpy as np

from mtcli.logger import setup_logger
from .model import calcular_profile, calcular_estatisticas, obter_rates

log = setup_logger()


def calcular_volume_profile(
    symbol,
    period,
    limit,
    step,
    volume,
    inicio=None,
    fim=None,
    verbose=False,
    timezone_str="America/Sao_Paulo",
    criterio_hvn="media",
):
    """
    Orquestra o cálculo completo do Volume Profile.

    Etapas:
    - Obtém candles históricos via MetaTrader 5
    - Calcula o Volume Profile por faixa de preço (High–Low)
    - Calcula estatísticas de Market Profile (POC, VA, HVN, LVN)
    - Converte datas para o fuso horário configurado

    Retorna estruturas prontas para consumo pela camada de visualização.
    """
    volume = volume.lower().strip()
    if volume not in ("tick", "real"):
        raise ValueError("Tipo de volume inválido. Use 'tick' ou 'real'.")

    rates = obter_rates(symbol, period, limit, inicio, fim)

    if rates is None or not isinstance(rates, np.ndarray) or len(rates) == 0:
        log.error("Nenhum dado retornado para o cálculo do Volume Profile.")
        return {}, {}, {}

    profile = calcular_profile(rates, step, volume)
    stats = calcular_estatisticas(profile, criterio=criterio_hvn)

    try:
        fuso = zoneinfo.ZoneInfo(timezone_str)
    except Exception:
        fuso = timezone(timedelta(hours=-3))

    try:
        inicio_real = datetime.utcfromtimestamp(float(rates[0]["time"])).astimezone(fuso)
        fim_real = datetime.utcfromtimestamp(float(rates[-1]["time"])).astimezone(fuso)
    except Exception:
        inicio_real = fim_real = "?"

    info = {
        "symbol": symbol,
        "period": period,
        "candles": len(rates),
        "inicio": str(inicio_real),
        "fim": str(fim_real),
        "timezone": timezone_str,
    }

    return profile, stats, info
