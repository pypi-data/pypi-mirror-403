from tgzr.hosts.harmony.plugin import HarmonyPlugin


class ThePanelPlugin(HarmonyPlugin):
    def __init__(self, ep):
        super().__init__(ep)
        self._panel = None

    def prepare_env(self, env: dict[str, str]) -> None:
        super().prepare_env(env)
        env["THE_PANEL_PLUGIN_ENV_VAR"] = "PLUGIN_A_VALUE"
        
    def install_gui(self) -> None:
        # NB: we can import this outside of this method
        # because Qt may not be initialized.
        from .gui import ThePanel
        self._panel = ThePanel()
        self._panel.show()

    def add_tab(self, widget, title)->None:
        self._panel.add_tab(widget, title)