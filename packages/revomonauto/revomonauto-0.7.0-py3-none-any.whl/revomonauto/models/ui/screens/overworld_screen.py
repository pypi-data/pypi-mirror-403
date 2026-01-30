from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import overworld_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class OverworldScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="overworld",
            elements={
                "current_time_text": overworld_elements.CurrentTimeText(),
                "day_time_pixel": overworld_elements.DayTimePixel(),
                "night_time_pixel": overworld_elements.NightTimePixel(),
                "main_menu_button": overworld_elements.MainMenuButton(),
                "main_menu_pixel": overworld_elements.MainMenuPixel(),
                "release_first_mon_button": overworld_elements.ReleaseFirstMonButton(),
                "release_first_mon_pixel": overworld_elements.ReleaseFirstMonPixel(),
                "aim_shoot_button": overworld_elements.AimShootButton(),
                "aim_shoot_pixel": overworld_elements.AimShootPixel(),
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(
        self,
        pymordial_controller: "PymordialController",
        pymordial_screenshot: bytes | None = None,
    ) -> bool:
        """
        Checks if the Revomon app is on the overworld screen.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.
            pymordial_screenshot (bytes | None, optional): Screenshot of the app. Defaults to None.

        Returns:
            bool: True if the app is on the overworld screen, False otherwise.
        """
        # Overworld Screen Scene
        self.logger.info("Checking if app is on the overworld screen...")
        if pymordial_screenshot is None:
            try:
                pymordial_screenshot = pymordial_controller.capture_screen()
            except Exception as e:
                self.logger.error(f"Failed to capture screenshot: {e}")
                return False

        main_menu_pixel = self.elements["main_menu_pixel"]
        release_first_mon_pixel = self.elements["release_first_mon_pixel"]
        aim_shoot_pixel = self.elements["aim_shoot_pixel"]

        try:
            result = all(
                [
                    pymordial_controller.is_element_visible(
                        pymordial_element=main_menu_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=release_first_mon_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=aim_shoot_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                ]
            )
        except Exception as e:
            self.logger.error(
                f"Failed to check if app is on the {self.name} screen: {e}"
            )
        self.logger.info(
            f"CURRENTLY ON the {self.name} screen."
            if result
            else f"NOT ON the {self.name} screen."
        )
        return result
