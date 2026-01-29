from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from tgzr.package_management.plugin_manager import PluginManager, Plugin

if TYPE_CHECKING:
    import click

_THE_PLUGIN_MANAGER = None


def get_plugin_manager():
    global _THE_PLUGIN_MANAGER
    if _THE_PLUGIN_MANAGER is None:
        _THE_PLUGIN_MANAGER = HarmonyPluginManager()

    return _THE_PLUGIN_MANAGER


class HarmonyPlugin(Plugin):

    @classmethod
    def plugin_type_name(cls) -> str:
        return "tgzr.hosts.harmony.plugin"

    def prepare_env(self, env: dict[str, str]):
        print(f"Preparing env for plugin {self.plugin_id()}")
        pass

    def install_cli(self, click_group: click.Group) -> None:
        pass

    def install(self):
        print(f"Installing Harmony plugin {self.plugin_id()}")

    def install_gui(self):
        print(f"Installing Harmony plugin GUI {self.plugin_id()}")


class HarmonyPluginManager(PluginManager[HarmonyPlugin]):
    EP_GROUP = "tgzr.hosts.harmony.plugin"

    def get_plugin(self, plugin_name: str) -> Optional[HarmonyPlugin]:
        for plugin in self.get_plugins():
            print(" ??", plugin.plugin_name(), plugin_name, "?")
            if plugin.plugin_name() == plugin_name:
                return plugin
        return None

    def report_loading(self):
        broken_plugins = self.get_broken_plugins()
        if broken_plugins:
            print(f"Got {len(broken_plugins)} error while loading plugins:")
            for ep, exception in broken_plugins:
                print(f"   ERROR at {ep}: {exception}")
        plugins = self.get_plugins()
        print(f"Found {len(plugins)} plugins at {self.EP_GROUP!r}:")
        for plugin in plugins:
            print("   ", plugin.plugin_id())

    def prepare_plugins_env(self, env: dict[str, str]):
        for plugin in self.get_plugins():
            plugin.prepare_env(env)

    def install_plugins_cli(self, click_group):
        for plugin in self.get_plugins():
            plugin.install_cli(click_group)
