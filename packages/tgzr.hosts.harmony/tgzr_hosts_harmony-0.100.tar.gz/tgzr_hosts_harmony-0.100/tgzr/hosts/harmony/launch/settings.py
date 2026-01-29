from pathlib import Path

import pydantic_settings
from pydantic import Field
import dotenv

ENVVAR_PREFIX = "tgzr_hosts_harmony_"


class HarmonyLaunchSettings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(env_prefix=ENVVAR_PREFIX)

    install_path: str = Field(
        "C:/Program Files (x86)/Toon Boom Animation/Toon Boom Harmony 25 Premium",
        description='The path where Harmony is installed. Must contain "win64/bin/\[harmony_exe_name\]")',
    )
    harmony_exe_name: str = Field(
        default="HarmonyPremium.exe", description="The name of your harmony executable."
    )
    ensure_system: bool = Field(
        True,
        description="Ensure your system is compatible (Only Windows is supported for now).",
    )

    @property
    def bin_path(self) -> Path:
        return Path(self.install_path) / "win64" / "bin"

    @property
    def execuable(self) -> Path:
        return self.bin_path / self.harmony_exe_name

    @property
    def harmony_python_packages_path(self) -> Path:
        return self.bin_path / "python-packages"


def get_settings() -> HarmonyLaunchSettings:
    f"""
    Returns a `HarmonyLaunchSettings()` with values from
    a .env file in the current directory (or ancestors) and
    environment variables.

    NB: env var use the prefix "{ENVVAR_PREFIX}"
    """
    dotenv_path = dotenv.find_dotenv(usecwd=True)
    return HarmonyLaunchSettings(_env_file=dotenv_path)  # type: ignore
