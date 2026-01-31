"""
Modelo de dados e cálculos do plugin mtcli-volume.

Este módulo contém:
- Acesso ao MetaTrader 5
- Cálculo do Volume Profile por faixa High–Low
- Cálculo de estatísticas de Market Profile (POC, VA, HVN, LVN)

Toda a lógica matemática e de mercado reside aqui.
"""

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime

import MetaTrader5 as mt5
import numpy as np

from mtcli.logger import setup_logger
from mtcli.mt5_context import mt5_conexao
from mtcli_volume.conf import DIGITOS

log = setup_logger()


def obter_rates(symbol: str, period: str, bars: int,
                data_inicio: datetime = None, data_fim: datetime = None):
    """
    Obtém candles históricos do MetaTrader 5.

    Pode buscar:
    - Um número fixo de candles
    - Um intervalo de datas específico

    Retorna um numpy.ndarray compatível com os cálculos do Volume Profile.
    """
    with mt5_conexao():
        tf = getattr(mt5, f"TIMEFRAME_{period.upper()}", None)
        if tf is None:
            log.error(f"Timeframe inválido: {period}")
            return None

        if not mt5.symbol_select(symbol, True):
            log.error(f"Erro ao selecionar símbolo {symbol}")
            return None

        try:
            if data_inicio and data_fim:
                rates = mt5.copy_rates_range(symbol, tf, data_inicio, data_fim)
            else:
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        except Exception as e:
            log.error(f"Erro ao obter dados históricos: {e}")
            return None

        if rates is None or len(rates) == 0:
            log.error("Nenhum dado retornado.")
            return None

    return rates


def calcular_profile(rates, step: float, volume_tipo: str = "tick"):
    """
    Calcula o Volume Profile distribuindo o volume do candle
    uniformemente entre todas as faixas de preço entre LOW e HIGH.

    Essa abordagem reduz o viés do preço de fechamento e se aproxima
    do Volume Profile clássico (VAP).
    """
    profile = defaultdict(float)

    for r in rates:
        if isinstance(r, Mapping):
            low, high = r["low"], r["high"]
            tick_volume = r["tick_volume"]
            real_volume = r.get("real_volume", tick_volume)

        elif isinstance(r, np.void):
            low, high = float(r["low"]), float(r["high"])
            tick_volume = int(r["tick_volume"])
            real_volume = int(r["real_volume"]) if "real_volume" in r.dtype.names else tick_volume

        else:
            raise TypeError(f"Formato de rate desconhecido: {type(r)}")

        volume = tick_volume if volume_tipo == "tick" else real_volume
        if high < low:
            low, high = high, low

        faixa_inicio = round(low // step * step, DIGITOS)
        faixa_fim = round(high // step * step, DIGITOS)

        faixas = []
        p = faixa_inicio
        while p <= faixa_fim:
            faixas.append(round(p, DIGITOS))
            p += step

        if not faixas:
            continue

        vol_por_faixa = volume / len(faixas)
        for f in faixas:
            profile[f] += vol_por_faixa

    return dict(profile)


def calcular_estatisticas(profile: dict, criterio: str = "media",
                          hvn_multiplicador: float = 1.5, lvn_multiplicador: float = 0.5,
                          percentil_hvn: int = 80, percentil_lvn: int = 20):
    """
    Calcula estatísticas clássicas de Market Profile:

    - POC (Point of Control)
    - Área de Valor (70%)
    - HVNs e LVNs com critérios profissionais
    """
    if not profile:
        return {"poc": None, "area_valor": (None, None), "hvns": [], "lvns": []}

    volumes = np.array(list(profile.values()))
    faixas = np.array(list(profile.keys()))

    idx = np.argsort(volumes)[::-1]
    volumes_ord = volumes[idx]
    faixas_ord = faixas[idx]

    poc = faixas_ord[0]

    total = volumes.sum()
    acumulado = 0
    area = []
    for f, v in zip(faixas_ord, volumes_ord):
        acumulado += v
        area.append(f)
        if acumulado >= total * 0.7:
            break

    area_valor = (min(area), max(area))
    media = volumes.mean()

    if criterio == "media":
        hvns = sorted(f for f, v in profile.items() if v >= media * hvn_multiplicador)
        lvns = sorted(f for f, v in profile.items() if v <= media * lvn_multiplicador)
    else:
        p_hvn = np.percentile(volumes, percentil_hvn)
        p_lvn = np.percentile(volumes, percentil_lvn)
        hvns = sorted(f for f, v in profile.items() if v >= p_hvn)
        lvns = sorted(f for f, v in profile.items() if v <= p_lvn)

    return {"poc": poc, "area_valor": area_valor, "hvns": hvns, "lvns": lvns}
