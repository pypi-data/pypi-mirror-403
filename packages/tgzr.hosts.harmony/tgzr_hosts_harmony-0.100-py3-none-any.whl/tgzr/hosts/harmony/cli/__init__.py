import sys
import platform

import click
import rich
import rich.table

from .._version import __version__
from .plugins_cli import plugins_cli
from .settings_cli import settings_cli


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="harcli")
def harcli(
    **kwargs,  # needed for plugin installing custom global options
):
    pass


harcli.add_command(settings_cli)
harcli.add_command(plugins_cli)


@harcli.command(help="Show infos about this installation.")
def info():
    table = rich.table.Table("Name", "Value")
    table.add_row("version", __version__)
    table.add_row("python version", ".".join([str(i) for i in sys.version_info]))
    table.add_row("sys.executable", sys.executable)
    table.add_row("platform.system", platform.system())
    rich.print(table)
