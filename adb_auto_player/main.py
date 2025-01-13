import logging
import multiprocessing
import sys
from typing import NoReturn

import eel
from eel.types import WebSocketT
from psutil import Process

import adb_auto_player.eel_functions as eel_functions

import adb_auto_player.plugin_loader as plugin_loader
from adb_auto_player.logging_setup import (
    update_logging_from_config,
    setup_logging,
    enable_frontend_logs,
)
import psutil
import platform
from pathlib import Path

ADB_WAS_RUNNING: bool = True


def terminate_adb() -> None:
    process = get_adb_process()
    if process is not None:
        process.terminate()


def get_adb_process() -> Process | None:
    adb_process_name = "adb.exe" if platform.system() == "Windows" else "adb"
    for process in psutil.process_iter(["name"]):
        if process.info["name"] == adb_process_name:
            return process
    return None


def close(page: str | None = None, sockets: list[WebSocketT] | None = None) -> NoReturn:
    global ADB_WAS_RUNNING
    if not ADB_WAS_RUNNING:
        terminate_adb()
    sys.exit(0)


def init_logs() -> None:
    setup_logging()
    main_config = plugin_loader.get_main_config()
    update_logging_from_config(main_config)
    enable_frontend_logs()


def init_eel() -> None:
    multiprocessing.freeze_support()
    eel_functions.init()
    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "frontend" / "build"  # type: ignore
        eel.init(str(path), [".svelte", ".html", ".js"])
    else:
        eel.init("frontend/src", [".svelte"])


def start() -> None:
    if getattr(sys, "frozen", False):
        eel.start(
            "",
            port=8888,
            host="localhost",
            mode="chrome",
            size=(1280, 720),
            close_callback=close,
        )
    else:
        eel.start(
            {"port": 5173},  # type: ignore
            port=8888,
            host="localhost",
            mode="chrome",
            size=(1280, 720),
            close_callback=close,
        )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    init_logs()

    if get_adb_process() is None:
        ADB_WAS_RUNNING = False

    init_eel()
    logging.error("Download new Version 1.0.0 for S3")
    logging.error("https://github.com/yulesxoxo/AdbAutoPlayer/releases")
    logging.error("This version cannot be updated to 1.0.0 please delete it")
    start()
