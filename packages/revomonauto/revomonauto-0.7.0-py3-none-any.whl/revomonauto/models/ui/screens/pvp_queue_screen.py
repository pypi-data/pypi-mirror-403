"""PVP Queue Screen for Revomon app.

Detects when the player is in the PVP matchmaking queue by checking for the
animated loading circle pixels around the PVP button.
"""

from logging import getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import main_menu_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class PvpQueueScreen(PymordialScreen):
    """PVP Queue screen - detects active matchmaking via loading circle pixels.

    The PVP loading animation shows 12 circles around the PVP button that
    animate from grey to white. We check 4 key positions (top, right, bottom, left).
    If 2+ are visible, we're in queue.
    """

    def __init__(self):
        super().__init__(
            name="pvp_queue",
            elements={
                "pvp_loading_pixel_top": main_menu_elements.PvpLoadingPixelTop(),
                "pvp_loading_pixel_right": main_menu_elements.PvpLoadingPixelRight(),
                "pvp_loading_pixel_bottom": main_menu_elements.PvpLoadingPixelBottom(),
                "pvp_loading_pixel_left": main_menu_elements.PvpLoadingPixelLeft(),
            },
        )
        self.logger = getLogger(__name__)

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """Check if PVP queue is active by detecting loading circle pixels."""
        self.logger.info("Checking if PVP queue is active...")

        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        loading_pixels = [
            self.elements["pvp_loading_pixel_top"],
            self.elements["pvp_loading_pixel_right"],
            self.elements["pvp_loading_pixel_bottom"],
            self.elements["pvp_loading_pixel_left"],
        ]

        try:
            visible_count = sum(
                1
                for pixel in loading_pixels
                if pymordial_controller.is_element_visible(
                    pymordial_element=pixel,
                    pymordial_screenshot=pymordial_screenshot,
                )
            )

            # If 2+ loading pixels visible, queue is active
            result = visible_count >= 2

            if result:
                self.logger.info(
                    f"PVP QUEUE ACTIVE ({visible_count}/4 loading pixels visible)"
                )
            else:
                self.logger.info(
                    f"PVP queue NOT active ({visible_count}/4 loading pixels visible)"
                )

            return result

        except Exception as e:
            self.logger.error(f"Failed to check PVP queue status: {e}")
            return False
