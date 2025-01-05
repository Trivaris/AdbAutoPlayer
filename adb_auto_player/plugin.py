from abc import abstractmethod
from pathlib import Path
from time import sleep, time
from typing import Any, TypeVar, Callable

from PIL import Image
from adbutils._device import AdbDevice

import adb_auto_player.adb as adb
import logging
import adb_auto_player.screen_utils as screen_utils
from adb_auto_player.config_constraint import ConfigConstraintType
from adb_auto_player.exceptions import UnsupportedResolutionException, TimeoutException


class Plugin:
    def __init__(self, device: AdbDevice, config: dict[str, Any]) -> None:
        self.device = device
        self.config = config
        self.store: dict[str, Any] = {}

    @abstractmethod
    def get_template_dir_path(self) -> Path:
        pass

    @abstractmethod
    def get_config_constraints(self) -> dict[str, ConfigConstraintType]:
        pass

    @abstractmethod
    def get_menu_options(self) -> list[dict[str, Any]]:
        pass

    def check_requirements(self) -> None:
        """
        :raises UnsupportedResolutionException:
        """
        resolution = adb.get_screen_resolution(self.device)
        supported_resolution = self.config.get("plugin", {}).get(
            "supported_resolution", "1080x1920"
        )
        if resolution != supported_resolution:
            raise UnsupportedResolutionException(
                f"This plugin only supports {supported_resolution}"
            )
        return None

    def find_first_template_center(
        self,
        template: str,
        threshold: float = 0.9,
        grayscale: bool = False,
        base_image: Image.Image | None = None,
    ) -> tuple[int, int] | None:
        template_path = self.get_template_dir_path() / template

        return screen_utils.find_center(
            self.device,
            template_path,
            threshold=threshold,
            grayscale=grayscale,
            base_image=base_image,
        )

    def find_all_template_centers(
        self, template: str, threshold: float = 0.9, grayscale: bool = False
    ) -> list[tuple[int, int]] | None:
        template_path = self.get_template_dir_path() / template

        return screen_utils.find_all_centers(
            self.device,
            template_path,
            threshold=threshold,
            grayscale=grayscale,
        )

    def wait_for_template(
        self,
        template: str,
        threshold: float = 0.9,
        grayscale: bool = False,
        delay: float = 1,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> tuple[int, int]:
        """
        :raises TimeoutException:
        """

        def find_template() -> tuple[int, int] | None:
            result = self.find_first_template_center(
                template,
                threshold=threshold,
                grayscale=grayscale,
            )
            if result is not None:
                logging.debug(f"{template} found")
            return result

        if timeout_message is None:
            timeout_message = (
                f"Could not find Template: '{template}' after {timeout} seconds"
            )

        return self.__execute_or_timeout(
            find_template, delay=delay, timeout=timeout, timeout_message=timeout_message
        )

    def wait_until_template_disappears(
        self,
        template: str,
        threshold: float = 0.9,
        grayscale: bool = False,
        delay: float = 1,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> None:
        """
        :raises TimeoutException:
        """

        def find_template() -> tuple[int, int] | None:
            result = self.find_first_template_center(
                template,
                threshold=threshold,
                grayscale=grayscale,
            )
            if result is None:
                logging.debug(f"{template} no longer visible")

            return result

        if timeout_message is None:
            timeout_message = (
                f"Template: {template} is still visible after {timeout} seconds"
            )

        self.__execute_or_timeout(
            find_template,
            delay=delay,
            timeout=timeout,
            timeout_message=timeout_message,
        )
        return None

    def wait_for_any_template(
        self,
        templates: list[str],
        threshold: float = 0.9,
        grayscale: bool = False,
        delay: float = 3,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> tuple[str, int, int]:
        """
        :raises TimeoutException:
        """

        def find_template() -> tuple[str, int, int] | None:
            return self.find_any_template_center(
                templates,
                threshold=threshold,
                grayscale=grayscale,
            )

        if timeout_message is None:
            timeout_message = (
                f"None of the templates {templates} were found after {timeout} seconds"
            )

        return self.__execute_or_timeout(
            find_template, delay=delay, timeout=timeout, timeout_message=timeout_message
        )

    def find_any_template_center(
        self,
        templates: list[str],
        threshold: float = 0.9,
        grayscale: bool = False,
    ) -> tuple[str, int, int] | None:
        base_image = screen_utils.get_screenshot(self.device)
        for template in templates:
            result = self.find_first_template_center(
                template,
                threshold=threshold,
                grayscale=grayscale,
                base_image=base_image,
            )
            if result is not None:
                x, y = result
                return template, x, y
        return None

    def press_back_button(self) -> None:
        self.device.keyevent(4)

    T = TypeVar("T")

    def __execute_or_timeout(
        self,
        operation: Callable[[], T | None],
        timeout_message: str,
        delay: float = 1,
        timeout: float = 30,
        result_should_be_none: bool = False,
    ) -> T:
        """
        :raises TimeoutException:
        """
        time_spent_waiting: float = 0
        end_time = time() + timeout
        end_time_exceeded = False

        while True:
            result = operation()
            if result_should_be_none and result is None:
                return None  # type: ignore
            elif result is not None:
                return result

            sleep(delay)
            time_spent_waiting += delay

            if time_spent_waiting >= timeout or end_time_exceeded:
                raise TimeoutException(f"{timeout_message}")

            if end_time <= time():
                end_time_exceeded = True
