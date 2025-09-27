"""ADB Auto Player Config Loader Module."""

import logging
import os
import platform
from functools import lru_cache
from pathlib import Path

from adb_auto_player.decorators import register_cache
from adb_auto_player.models.decorators import CacheGroup
from adb_auto_player.models.pydantic.general_settings import GeneralSettings


class ConfigLoader:
    """Utility class for resolving and caching important configuration paths."""

    @staticmethod
    @lru_cache(maxsize=1)
    def working_dir() -> Path:
        """Return the current working directory."""
        working_dir = Path.cwd()
        try:
            parts = working_dir.parts
            if "python" in parts and "tests" in parts:
                python_index = parts.index("python")
                tests_index = parts.index("tests")
                if tests_index == python_index + 1:
                    # Rebuild the path up to 'python'
                    return Path(*parts[: python_index + 1])
        except ValueError:
            pass
        return working_dir

    @staticmethod
    @lru_cache(maxsize=1)
    def config_dir() -> Path:
        """Return the absolute directory that should contain the main config."""
        system = platform.system()
        if system == "Linux":
            config_dir = Path.home() / ".config" / "adbautoplayer"
        elif system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                config_dir = Path(appdata) / "AdbAutoPlayer"
            else:
                config_dir = Path.home() / "AppData" / "Roaming" / "AdbAutoPlayer"
        elif system == "Darwin":
            config_dir = (
                Path.home()
                / "Library"
                / "Application Support"
                / "AdbAutoPlayer"
            )
        else:
            config_dir = Path.home() / ".adbautoplayer"

        resolved = config_dir.expanduser().absolute()
        logging.debug(f"Resolved config directory: {resolved}")
        try:
            resolved.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logging.debug(f"Unable to ensure config directory exists: {exc}")
        return resolved

    @staticmethod
    @lru_cache(maxsize=1)
    def games_dir() -> Path:
        """Determine and return the resource games directory."""
        working_dir = ConfigLoader.working_dir()
        linux_candidates: list[Path] = []
        if platform.system() == "Linux":
            linux_candidates = [
                Path.home()
                / ".config"
                / "adbautoplayer"
                / "python"
                / "adb_auto_player"
                / "games",
                Path.home()
                / ".config"
                / "adbautoplayer"
                / "games",
            ]

        candidates: list[Path] = [
            *linux_candidates,
            working_dir / "games",  # Windows GUI .exe, PyCharm
            working_dir.parent / "games",  # Windows CLI .exe
            working_dir / "adb_auto_player" / "games",  # uv
            working_dir.parent / "Resources" / "games",  # MacOS .app Bundle
        ]
        games_dir = next((c for c in candidates if c.exists()), candidates[0])
        logging.debug(f"Resolved resource games directory: {games_dir}")
        return games_dir

    @staticmethod
    @lru_cache(maxsize=1)
    def user_games_dir() -> Path:
        """Return the user-writable games configuration directory."""
        games_dir = ConfigLoader.config_dir() / "games"
        logging.debug(f"Resolved user games directory: {games_dir}")
        try:
            games_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logging.debug(f"Unable to ensure user games directory exists: {exc}")
        return games_dir

    @staticmethod
    @lru_cache(maxsize=1)
    def binaries_dir() -> Path:
        """Return the binaries directory."""
        return ConfigLoader.games_dir().parent / "binaries"

    @staticmethod
    @register_cache(CacheGroup.GENERAL_SETTINGS)
    @lru_cache(maxsize=1)
    def general_settings() -> GeneralSettings:
        """Locate and load the general settings config.toml file."""
        config_toml_path = ConfigLoader.config_dir() / "config.toml"
        logging.debug(f"Python config.toml path: {config_toml_path}")
        return GeneralSettings.from_toml(config_toml_path)
