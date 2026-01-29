from typing import Optional
import subprocess

import click
import rich
import rich.table

from ..launch.settings import get_settings


@click.group(name="settings", help="Settings management")
def settings_cli():
    pass


@settings_cli.command(help="Show info about installed plugins")
def show():
    settings = get_settings()
    table = rich.table.Table("Name", "Value", "Default", "Description")

    for name, field in type(settings).model_fields.items():
        value = getattr(settings, name)
        default = field.default
        table.add_row(name, str(value), str(default), field.description)

    rich.print(table)
