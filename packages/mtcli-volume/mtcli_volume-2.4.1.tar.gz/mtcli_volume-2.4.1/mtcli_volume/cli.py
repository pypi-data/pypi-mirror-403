"""
Interface de linha de comando (CLI) do plugin mtcli-volume.

Este módulo define o comando `vp`, responsável por:
- Interpretar argumentos do usuário via Click
- Validar parâmetros de entrada
- Acionar o controller para cálculo do Volume Profile
- Delegar a exibição dos resultados para a view

Não contém lógica de cálculo nem regras de negócio.
"""

from datetime import datetime

import click

from .conf import (
    FIM,
    INICIO,
    LIMIT,
    PERIOD,
    RANGE,
    SYMBOL,
    TIMEZONE,
    VOLUME,
)
from .controller import calcular_volume_profile
from .view import exibir_volume_profile


@click.command(
    help=(
        "Exibe o Volume Profile distribuindo o volume dos candles "
        "uniformemente entre as faixas de preço entre LOW e HIGH."
    )
)
@click.version_option(package_name="mtcli-volume")
@click.option("--symbol", "-s", default=SYMBOL, show_default=True, help="Símbolo do ativo.")
@click.option("--period", "-p", default=PERIOD, show_default=True, help="Timeframe utilizado no cálculo.")
@click.option("--limit", "-l", default=LIMIT, show_default=True, help="Quantidade de candles analisados.")
@click.option("--range", "-r", type=float, default=RANGE, show_default=True, help="Tamanho da faixa de preço.")
@click.option("--volume", "-v", type=click.Choice(["tick", "real"], case_sensitive=False),
              default=VOLUME, show_default=True, help="Tipo de volume utilizado.")
@click.option("--inicio", "-i", default=INICIO, show_default=True, help="Data/hora inicial (YYYY-MM-DD HH:MM).")
@click.option("--fim", "-f", default=FIM, show_default=True, help="Data/hora final (YYYY-MM-DD HH:MM).")
@click.option("--timezone", "-tz", default=TIMEZONE, show_default=True, help="Fuso horário para exibição.")
@click.option("--hvn-criterio", type=click.Choice(["media", "percentil"], case_sensitive=False),
              default="percentil", show_default=True, help="Critério para definição de HVNs/LVNs.")
@click.option("--verbose", "-vv", is_flag=True, help="Exibe informações detalhadas da análise.")
def volume(
    symbol,
    period,
    limit,
    range,
    volume,
    inicio,
    fim,
    timezone,
    hvn_criterio,
    verbose,
):
    """
    Executa o cálculo e a exibição do Volume Profile.

    O Volume Profile é calculado distribuindo o volume de cada candle
    igualmente entre todas as faixas de preço compreendidas entre
    o LOW e o HIGH do candle.

    Esta abordagem fornece uma representação mais precisa da
    concentração de volume ao longo do eixo de preços.
    """
    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d %H:%M") if inicio else None
    fim_dt = datetime.strptime(fim, "%Y-%m-%d %H:%M") if fim else None

    profile, stats, info = calcular_volume_profile(
        symbol=symbol,
        period=period,
        limit=limit,
        step=range,
        volume=volume,
        inicio=inicio_dt,
        fim=fim_dt,
        verbose=verbose,
        timezone_str=timezone,
        criterio_hvn=hvn_criterio.lower(),
    )

    exibir_volume_profile(profile, stats, symbol, info, verbose)
