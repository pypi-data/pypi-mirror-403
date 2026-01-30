from logging import getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import wardrobe_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class WardrobeScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="wardrobe",
            elements={
                "change_wardrobe_tab_right_pixel": wardrobe_elements.ChangeWardrobeTabRightPixel(),
                "change_wardrobe_tab_left_pixel": wardrobe_elements.ChangeWardrobeTabLeftPixel(),
                "item_1_wear_pixel": wardrobe_elements.Item1WearPixel(),
                "item_2_wear_pixel": wardrobe_elements.Item2WearPixel(),
                "item_3_wear_pixel": wardrobe_elements.Item3WearPixel(),
                "item_4_wear_pixel": wardrobe_elements.Item4WearPixel(),
                "item_5_wear_pixel": wardrobe_elements.Item5WearPixel(),
                "change_wardrobe_page_left_pixel": wardrobe_elements.ChangeWardrobePageLeftPixel(),
                "change_wardrobe_page_right_pixel": wardrobe_elements.ChangeWardrobePageRightPixel(),
            },
        )
        self.logger = getLogger(__name__)

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """
        Checks if the Revomon app is on the wardrobe screen.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.

        Returns:
            bool: True if the app is on the wardrobe screen, False otherwise.
        """
        # Wardrobe Screen Scene
        self.logger.info("Checking if app is on the wardrobe screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        change_wardrobe_tab_right_pixel = self.elements[
            "change_wardrobe_tab_right_pixel"
        ]
        change_wardrobe_tab_left_pixel = self.elements["change_wardrobe_tab_left_pixel"]
        try:
            result = all(
                [
                    pymordial_controller.is_element_visible(
                        pymordial_element=change_wardrobe_tab_right_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=change_wardrobe_tab_left_pixel,
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
            f"Currently ON the {self.name} screen."
            if result
            else f"Currently NOT ON the {self.name} screen."
        )
        return result
