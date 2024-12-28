import shutil
import sys
import tomllib
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from packaging.version import Version

import logging

RELEASE_API_URL = f"https://api.github.com/repos/yulesxoxo/AdbAutoPlayer/releases/latest"
PYPROJECT_VERSION: str | None = None
LATEST_RELEASE_JSON: dict[str, Any] | None = None


def __get_project_dir() -> Path:
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) # type: ignore
    else:
        path = Path.cwd()
    logging.debug(f"Project dir: {path}")
    return path


def __get_pyproject_toml_path() -> Path:
    if getattr(sys, "frozen", False):
        return __get_project_dir() / "pyproject.toml"
    else:
        return  Path.cwd().parent / "pyproject.toml"


def __get_version_from_pyproject() -> str:
    global PYPROJECT_VERSION
    if PYPROJECT_VERSION is not None:
        return PYPROJECT_VERSION

    with open(__get_pyproject_toml_path(), "rb") as f:
        pyproject_toml_file = tomllib.load(f)

    PYPROJECT_VERSION = str(pyproject_toml_file["tool"]["poetry"]["version"])
    return PYPROJECT_VERSION


def __get_latest_release_json() -> dict[str, Any] | None:
    """Fetch the latest release information from the GitHub API"""
    global LATEST_RELEASE_JSON
    if LATEST_RELEASE_JSON is not None:
        return LATEST_RELEASE_JSON

    response = requests.get(RELEASE_API_URL)
    if response.status_code != 200:
        logging.debug(f"Failed to fetch latest release: {response.status_code}, {response.text}")
        return None

    LATEST_RELEASE_JSON = response.json()
    return LATEST_RELEASE_JSON


def __get_latest_version() -> str | None:
    release_json = __get_latest_release_json()
    if release_json is None:
        logging.error("Could not fetch the latest release")
        return None

    return str(release_json["tag_name"])


def __get_plugins_zip_url() -> str | None:
    release_json = __get_latest_release_json()
    if release_json is None:
        logging.error("Could not fetch the latest release")
        return None

    for asset in release_json.get("assets", []):
        if asset["name"] == "plugins.zip":
            return str(asset["browser_download_url"])

    return None


def __get_version_from_version_check_file() -> str | None:
    version_check_path = __get_project_dir() / "VERSION_CHECK"
    if version_check_path.exists():
        with version_check_path.open() as f:
            return f.read().strip()

    return None


def __get_last_checked_version() -> str:
    """Get the version from the VERSION_CHECK file or fallback to pyproject version."""
    version_check = __get_version_from_version_check_file()
    pyproject_version = __get_version_from_pyproject()
    if version_check is None:
        return pyproject_version
    return (
        version_check
        if Version(version_check) > Version(pyproject_version)
        else pyproject_version
    )


def __is_new_version_available() -> bool:
    """Check if a new version of the software is available."""
    last_checked_version = __get_last_checked_version()
    latest_version = __get_latest_version()
    if latest_version is None:
        return False

    return Version(last_checked_version) < Version(latest_version)


def __download_and_extract_plugins(url: str) -> bool:
    """Download and extract plugins from the given URL."""
    response = requests.get(url)
    if response.status_code != 200:
        return False

    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(__get_project_dir() / "tmp")
        return True


def __install_compatible_plugins() -> bool | None:
    base_dir = __get_project_dir() / "tmp" / "plugins"
    if not base_dir.exists():
        logging.debug(f"The directory {base_dir} does not exist")
        return None

    all_plugins_installed: bool = True
    for dir_name in list(base_dir.iterdir()): # type: Path
        dir_path = base_dir / dir_name
        config_path = dir_path / "config.toml"

        if not config_path.exists():
            logging.debug(f"Config missing: {config_path}")
            continue

        try:
            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
        except Exception as e:
            logging.debug(f"Exception while installing plugin: {e}")
            continue

        min_adb_auto_player_version: str | None = config_data.get("plugin", {}).get(
            "min_adb_auto_player_version"
        )
        if min_adb_auto_player_version is None:
            continue
        if Version(min_adb_auto_player_version) <= Version(
            __get_version_from_pyproject()
        ):
            __install_plugin_from_tmp(dir_path)
        else:
            all_plugins_installed = False

    return all_plugins_installed


def __backup_existing_config(plugin_dir: Path) -> None:
    """
    TODO update existing config instead of copying.
    """
    config_path = plugin_dir / "config.toml"
    backup_config_path = plugin_dir / "config_backup.toml"

    if config_path.exists():
        shutil.copy2(config_path, backup_config_path)


def __install_plugin_from_tmp(dir_path: Path) -> None:
    plugin_dir = __get_project_dir() / "plugins" / dir_path.name
    plugin_dir.mkdir(parents=True, exist_ok=True)

    __backup_existing_config(plugin_dir)

    for item in list(dir_path.iterdir()): # type: Path
        source_item = dir_path / item.name
        dest_item = plugin_dir / item.name

        if source_item.is_dir():
            shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy2(source_item, dest_item)

    logging.info(f"Plugin updated: {dir_path.name}")


def __update_plugins() -> None | bool:
    if not __is_new_version_available():
        return None

    latest_version = __get_latest_version()
    browser_download_url = __get_plugins_zip_url()

    if latest_version is None or browser_download_url is None:
        return None

    if not __download_and_extract_plugins(browser_download_url):
        return None

    with open(__get_project_dir() / "VERSION_CHECK", "w") as version_file:
        version_file.write(latest_version)

    all_plugins_installed = __install_compatible_plugins()
    shutil.rmtree(__get_project_dir() / "tmp")
    return all_plugins_installed


def run_self_updater() -> None:
    version = __get_version_from_pyproject()
    if version == "0.0.0":
        logging.info("Skipping updater for dev")
        return
    logging.info(f"App Version: {version}")
    result = __update_plugins()
    if result is None:
        logging.info("No new updates")
    elif result is not None and not result:
        logging.warning(
            ".exe or binary needs to be updated: "
            "https://github.com/yulesxoxo/AdbAutoPlayer/releases/latest"
        )
    else:
        logging.info("Plugins updated successfully")
        logging.warning(
            "Your plugin configs have been reset, "
            "backups were saved as 'config_backup.toml'"
        )
