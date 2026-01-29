from typing import Optional
import subprocess

import click
import rich
import rich.table

from ..plugin import get_plugin_manager


def run_uv_cmd(cmd: list[str]) -> int:
    import uv

    uv = uv.find_uv_bin()
    cmd = [uv] + cmd
    print(f"Executing uv cmd: {' '.join(cmd)}")
    return subprocess.call(cmd)


@click.group(name="plugins", help="Plugin management")
def plugins_cli():
    pass


@plugins_cli.command(help="Show info about installed plugins")
def show():
    pm = get_plugin_manager()

    table = rich.table.Table("Plugin", "Loaded", "Error")
    for plugin in pm.get_plugins():
        table.add_row(plugin.plugin_name(), "✅", "")
    for ep, exception in pm.get_broken_plugins():
        table.add_row(f"{ep.name} = {ep.value}", "❌", str(exception))
    rich.print(table)


@plugins_cli.command(help="Install more plugins")
@click.argument("plugins", nargs=-1)
@click.option("-f", "--folder-index", help="Look for packages in this folder")
@click.option("-i", "--index", help="Look for packages at this package index url")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Perform a dry run, i.e., don't actually install anything but resolve the dependencies and print the resulting plan",
)
def install(
    plugins: tuple[str, ...],
    folder_index: Optional[str],
    index: Optional[str],
    dry_run: bool,
):
    """
    Install plugin(s) (or any package) in this virtual env.
    """
    if not plugins:
        raise click.UsageError("Please provide at least on plugin name to install.")

    uv_options = []
    if dry_run:
        uv_options.append("--dry-run")
    if folder_index is not None:
        uv_options.append("--find-links")
        uv_options.append(folder_index)
    if index is not None:
        uv_options.append("--index")
        uv_options.append(index)
    cmd = ["pip", "install", *uv_options, "-U", *plugins]
    run_uv_cmd(cmd)


@plugins_cli.command(help="Uninstall some plugins")
@click.argument("plugins", nargs=-1)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Perform a dry run, i.e., don't actually install anything but resolve the dependencies and print the resulting plan",
)
def uninstall(
    plugins: tuple[str, ...],
    dry_run: bool,
):
    """
    Uninstall plugin(s) (or any package) from this virtual env.
    """
    if not plugins:
        raise click.UsageError("Please provide at least on plugin name to install.")

    uv_options = []
    if dry_run:
        uv_options.append("--dry-run")
    cmd = ["pip", "uninstall", *uv_options, " ".join(plugins)]
    run_uv_cmd(cmd)
