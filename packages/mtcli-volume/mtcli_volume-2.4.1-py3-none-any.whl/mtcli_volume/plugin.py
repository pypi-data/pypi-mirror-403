"""
Módulo de integração do plugin mtcli-volume com o mtcli.

Este módulo é responsável por registrar o comando do plugin
na aplicação principal `mtcli`, permitindo que o Volume Profile
seja acessado via linha de comando.

Nenhuma lógica de cálculo ou apresentação reside aqui.
"""

from .cli import volume


def register(cli):
    """
    Registra o comando do Volume Profile no mtcli.

    Este método é chamado automaticamente pelo mtcli durante
    o carregamento de plugins.

    :param cli: Instância principal do CLI do mtcli
    """
    cli.add_command(volume, name="vp")
