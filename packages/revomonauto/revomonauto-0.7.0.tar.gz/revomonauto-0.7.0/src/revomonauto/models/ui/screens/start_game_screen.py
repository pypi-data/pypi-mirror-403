from logging import getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import start_game_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class StartGameScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="start_game",
            elements={
                "start_game_button": start_game_elements.StartGameButton(),
                "start_game_pixel": start_game_elements.StartGamePixel(),
                "quality_decrease_button": start_game_elements.QualityDecreaseButton(),
                "quality_decrease_pixel": start_game_elements.QualityDecreasePixel(),
                "quality_increase_button": start_game_elements.QualityIncreaseButton(),
                "quality_increase_pixel": start_game_elements.QualityIncreasePixel(),
                "current_quality_text": start_game_elements.CurrentQualityText(),
                "current_version_text": start_game_elements.CurrentVersionText(),
                "game_update_text": start_game_elements.GameUpdateText(),
                "revomon_badge_pixel": start_game_elements.RevomonBadgePixel(),
            },
        )
        self.logger = getLogger(__name__)

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """
        Checks if the Revomon app is on the start game screen.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.

        Returns:
            bool: True if the app is on the start game screen, False otherwise.
        """
        # Start Game Screen Scene
        self.logger.info("Checking if app is on the start game screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False
        # Convert screenshot to bytes for is_element_visible
        screenshot_bytes: bytes | None = None
        try:
            import io

            from numpy import ndarray
            from PIL import Image

            if isinstance(pymordial_screenshot, ndarray):
                img = Image.fromarray(pymordial_screenshot)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                screenshot_bytes = buf.getvalue()
            elif isinstance(pymordial_screenshot, bytes):
                screenshot_bytes = pymordial_screenshot
        except Exception as e:
            self.logger.warning(f"Failed to convert screenshot: {e}")
            if isinstance(pymordial_screenshot, bytes):
                screenshot_bytes = pymordial_screenshot

        start_game_pixel = self.elements["start_game_pixel"]
        quality_decrease_pixel = self.elements["quality_decrease_pixel"]
        quality_increase_pixel = self.elements["quality_increase_pixel"]
        revomon_badge_pixel = self.elements["revomon_badge_pixel"]

        try:
            # Check each pixel individually for debugging
            start_game_visible = pymordial_controller.is_element_visible(
                pymordial_element=start_game_pixel,
                pymordial_screenshot=screenshot_bytes,
            )
            self.logger.debug(f"start_game_pixel visible: {start_game_visible}")

            quality_decrease_visible = pymordial_controller.is_element_visible(
                pymordial_element=quality_decrease_pixel,
                pymordial_screenshot=screenshot_bytes,
            )
            self.logger.debug(
                f"quality_decrease_pixel visible: {quality_decrease_visible}"
            )

            quality_increase_visible = pymordial_controller.is_element_visible(
                pymordial_element=quality_increase_pixel,
                pymordial_screenshot=screenshot_bytes,
            )
            self.logger.debug(
                f"quality_increase_pixel visible: {quality_increase_visible}"
            )

            revomon_badge_visible = pymordial_controller.is_element_visible(
                pymordial_element=revomon_badge_pixel,
                pymordial_screenshot=screenshot_bytes,
            )
            self.logger.debug(f"revomon_badge_pixel visible: {revomon_badge_visible}")

            result = all(
                [
                    start_game_visible,
                    quality_decrease_visible,
                    quality_increase_visible,
                    revomon_badge_visible,
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
