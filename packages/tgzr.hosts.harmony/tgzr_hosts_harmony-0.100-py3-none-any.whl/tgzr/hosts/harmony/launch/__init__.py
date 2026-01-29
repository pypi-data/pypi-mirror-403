from __future__ import annotations

import os
import sys
import platform
from pathlib import Path
import subprocess

from .. import external_script_packages_folder
from ..plugin import get_plugin_manager
from .settings import get_settings, HarmonyLaunchSettings


def prepare_env(settings: HarmonyLaunchSettings) -> dict[str, str]:
    if sys.version_info[:2] != (3, 9):
        raise RuntimeError("You need a python 3.9 to use this :/")

    if settings.ensure_system:
        system = platform.system()
        if system != "Windows":
            raise RuntimeError(f"Sorry, {system} not supported yet :/")

    env = os.environ.copy()
    env["TB_EXTERNAL_SCRIPT_PACKAGES_FOLDER"] = str(
        Path(external_script_packages_folder.__file__).parent
    )

    return env


def start_process(cmd, env):
    print("Running process:", cmd)
    subprocess.run(cmd, check=True, env=env)


def harmony():
    pm = get_plugin_manager()
    pm.report_loading()

    settings = get_settings()
    env = prepare_env(settings)
    pm.prepare_plugins_env(env)

    cmd = f"{settings.execuable}"
    # print(f"Launching Harmony: {settings.execuable}")
    start_process(cmd, env)


def harpy():
    pm = get_plugin_manager()
    pm.report_loading()

    settings = get_settings()
    env = prepare_env(settings)
    pm.prepare_plugins_env(env)

    python = sys.executable
    from .. import startup

    cmd = (
        f'{python} -i -c "import {startup.__name__} as startup; startup.startup_py() "'
    )
    start_process(cmd, env)


def harcli():
    pm = get_plugin_manager()

    settings = get_settings()
    # env = prepare_env(settings)
    # pm.prepare_plugins_env(env)

    from ..cli import harcli

    pm.install_plugins_cli(harcli)

    sys.exit(harcli())
