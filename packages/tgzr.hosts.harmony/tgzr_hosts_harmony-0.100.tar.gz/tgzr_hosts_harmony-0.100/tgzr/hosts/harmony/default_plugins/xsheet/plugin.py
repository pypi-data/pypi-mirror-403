from __future__ import annotations
from typing import TYPE_CHECKING

from tgzr.hosts.harmony.plugin import HarmonyPlugin, get_plugin_manager

from . import cli

if TYPE_CHECKING:
    import click


class XSheetPlugin(HarmonyPlugin):

    def install_gui(self) -> None:
        from .gui import XSheetPanel

        the_panel_plugin_name = (
            "tgzr.hosts.harmony.default_plugins.the_panel.plugin.ThePanelPlugin"
        )
        the_panel = get_plugin_manager().get_plugin(the_panel_plugin_name)
        if the_panel is not None:
            the_panel.add_tab(XSheetPanel(), "XSheet")  # type: ignore

    def install_cli(self, click_group: click.Group) -> None:
        cli.install_in_group(click_group)
