from logging import getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ...strategies import RevomonTextStrategy
from ..elements import shared_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class MarketScreen(PymordialScreen):
    """Market Screen for Revomon app.

    Note: Market uses a different title position than other submenus.
    """

    def __init__(self):
        super().__init__(
            name="market",
            elements={
                "market_title_text": shared_elements.MarketTitleText(),
            },
        )
        self.logger = getLogger(__name__)
        self.expected_title = "marketplace"  # Full title is "Marketplace"

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """Check if on the market screen via OCR text detection."""
        self.logger.info(f"Checking if app is on the {self.name} screen...")

        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        try:
            title_element = self.elements["market_title_text"]
            cropped_imgs = pymordial_controller.revomon.extract_regions(
                pymordial_elements=[title_element],
                image=pymordial_screenshot,
            )

            result = pymordial_controller.read_text(
                cropped_imgs[0],
                case_sensitive=False,
                strategy=RevomonTextStrategy(),
            )

            # DEBUG: Log what OCR reads
            self.logger.debug(f"OCR result for {self.name}: {result}")

            for text in result:
                if self.expected_title in text.lower():
                    self.logger.info(f"CURRENTLY ON the {self.name} screen.")
                    return True

            self.logger.info(f"NOT ON the {self.name} screen. OCR read: {result}")
            return False

        except Exception as e:
            self.logger.error(
                f"Failed to check if app is on the {self.name} screen: {e}"
            )
            return False
