from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import revocenter_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class RevocenterScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="revocenter",
            elements={
                "clerk_npc_button": revocenter_elements.clerk_npc_button,
                "clerk_npc_pixel": revocenter_elements.clerk_npc_pixel,
                "nurse_npc_button": revocenter_elements.nurse_npc_button,
                "nurse_npc_pixel": revocenter_elements.nurse_npc_pixel,
                "move_tutor_npc_button": revocenter_elements.move_tutor_npc_button,
                "move_tutor_npc_pixel": revocenter_elements.move_tutor_npc_pixel,
                "tv_screen_button": revocenter_elements.tv_screen_button,
                "tv_screen_pixel": revocenter_elements.tv_screen_pixel,
                "tv_screen_drassius_button": revocenter_elements.tv_screen_drassius_button,
                "drassius_nurse_npc_pixel": revocenter_elements.drassius_nurse_npc_pixel,
                "green_sign_pixel": revocenter_elements.green_sign_pixel,
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(
        self,
        pymordial_controller: "PymordialController",
        pymordial_screenshot: bytes | None = None,
    ) -> bool:
        """
        Checks if the Revomon app is inside a Revocenter.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.
            pymordial_screenshot (bytes | None, optional): Screenshot of the app. Defaults to None.

        Returns:
            bool: True if the app is in a Revocenter, False otherwise.
        """
        self.logger.info("Checking if app is in a Revocenter...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        clerk_npc_pixel = self.elements["clerk_npc_pixel"]
        green_sign_pixel = self.elements["green_sign_pixel"]

        try:
            result = all(
                [
                    pymordial_controller.is_element_visible(
                        pymordial_element=green_sign_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=clerk_npc_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                ]
            )
        except Exception as e:
            self.logger.error(
                f"Failed to check if app is on the {self.name} screen: {e}"
            )
            return False
        self.logger.info(
            f"CURRENTLY ON the {self.name} screen."
            if result
            else f"NOT ON the {self.name} screen."
        )
        return result
