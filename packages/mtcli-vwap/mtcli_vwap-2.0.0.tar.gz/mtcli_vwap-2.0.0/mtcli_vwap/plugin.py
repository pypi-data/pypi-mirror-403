"""Plugin VWAP para o mtcli."""

from .cli import vwap


def register(cli):
    """Registra o comando vwap na CLI principal."""
    cli.add_command(vwap, name="vwp")
