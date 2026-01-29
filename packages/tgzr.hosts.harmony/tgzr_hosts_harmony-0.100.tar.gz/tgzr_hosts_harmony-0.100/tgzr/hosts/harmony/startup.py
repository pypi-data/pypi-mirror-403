
from .plugin import get_plugin_manager

from .launch.settings import get_settings
import sys

def startup_gui():
    """
    Must be called in harmony gui session to setup the 
    environment.
    """
    print("Installing Plugins.")
    plugin_manager = get_plugin_manager()
    for plugin in plugin_manager.get_plugins():
        plugin.install()
        plugin.install_gui()

def startup_py():
    print("✨ HARPY STARTUP ✨")
    print("Installing Plugins.")
    plugin_manager = get_plugin_manager()
    for plugin in plugin_manager.get_plugins():
        plugin.install()

    settings = get_settings()

    # We add harmony packages path to PYTHON_PATH to be able
    # to import ToonBoom.harmony:
    sys.path.insert(0, str(settings.harmony_python_packages_path))

    try:
        from ToonBoom import harmony
    except ImportError as err:
        print(f"!!! Error loading harmony: {err}")
    else:
        print(f"Harmony available with \"from ToonBoom import harmony\"")
