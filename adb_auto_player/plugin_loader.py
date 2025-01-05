import hashlib
import importlib.util
import json
import sys
import tomllib
from pathlib import Path

import toml
import types
from typing import Any, cast

import logging

PLUGIN_LIST_FILE = "plugin_list.json"
PLUGIN_CONFIG_FILE = "config.toml"
MAIN_CONFIG_FILE = "main_config.toml"


def __get_project_dir() -> Path:
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS).parent  # type: ignore
    else:
        path = Path.cwd()
    logging.debug(f"Project dir: {path}")
    return path


def get_plugins_dir() -> Path:
    return __get_project_dir() / "plugins"


def get_main_config() -> dict[str, Any]:
    with open(__get_project_dir() / MAIN_CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def __scan_plugins() -> list[dict[str, Any]]:
    plugins = []

    for plugin_path in get_plugins_dir().iterdir():  # type: Path
        config = load_config(plugin_path.name)

        if config:
            plugin_config = config.get("plugin", {})
            packages = plugin_config.get("packages")
            name = plugin_config.get("name")
            plugin = {"packages": packages, "name": name, "dir": plugin_path.name}
            plugins.append(plugin)

    return plugins


def __generate_plugin_list_hash() -> str:
    hash_md5 = hashlib.md5()

    plugins_dir = get_plugins_dir()

    for plugin_path in plugins_dir.iterdir():  # type: Path
        config_file = plugin_path / PLUGIN_CONFIG_FILE

        if config_file.is_file():
            hash_md5.update(str(config_file.stat().st_mtime).encode("utf-8"))

    return hash_md5.hexdigest()


def load_plugin_configs() -> list[dict[str, Any]]:
    path = __get_project_dir() / PLUGIN_LIST_FILE
    if path.exists():
        with open(path, "r") as f:
            cached_plugins = json.load(f)

        if cached_plugins.get("hash") == __generate_plugin_list_hash():
            return cast(list[dict[str, Any]], cached_plugins["plugins"])

    plugins = __scan_plugins()
    __create_plugin_list_file(plugins)

    return plugins


def __create_plugin_list_file(plugins: list[dict[str, Any]]) -> None:
    plugin_data = {"hash": __generate_plugin_list_hash(), "plugins": plugins}

    with open(__get_project_dir() / PLUGIN_LIST_FILE, "w") as f:
        json.dump(plugin_data, f, indent=4)


def load_config(plugin_dir: str) -> dict[str, Any] | None:
    config_file = get_plugins_dir() / plugin_dir / PLUGIN_CONFIG_FILE
    if not config_file.exists():
        return None
    with open(config_file, "rb") as f:
        return tomllib.load(f)


def save_config_for_plugin(config: dict[str, Any], plugin_dir: str) -> None:
    config_file = get_plugins_dir() / plugin_dir / PLUGIN_CONFIG_FILE
    with open(config_file, "w") as f:
        toml.dump(config, f)


def load_plugin_module(plugin_name: str) -> types.ModuleType:
    """
    :raises ValueError: When module spec could not be loaded
    """
    plugin_main_path = get_plugins_dir() / plugin_name / "run.py"
    logging.debug(f"Loading plugin module: {plugin_main_path}")

    spec = importlib.util.spec_from_file_location(plugin_name, plugin_main_path)
    if spec is None:
        raise ValueError("Failed to load module spec")

    module = importlib.util.module_from_spec(spec)

    sys.modules[plugin_name] = module

    loader = spec.loader
    if loader is None:
        raise ValueError("Failed to load spec loader")

    loader.exec_module(module)

    return module


def get_plugin_for_app(
    plugins: list[dict[str, Any]], app: str
) -> dict[str, Any] | None:
    for plugin in plugins:
        if app in plugin.get("packages", {}):
            return plugin
    return None


def save_config(config: dict[str, Any]) -> None:
    with open(__get_project_dir() / MAIN_CONFIG_FILE, "w") as f:
        toml.dump(config, f)
