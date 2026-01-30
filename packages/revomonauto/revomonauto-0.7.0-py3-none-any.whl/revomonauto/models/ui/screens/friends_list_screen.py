from logging import getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ...strategies import RevomonTextStrategy
from ..elements import shared_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class FriendsListScreen(PymordialScreen):
    """Friends List Screen for Revomon app."""

    def __init__(self):
        super().__init__(
            name="friends_list",
            elements={
                "submenu_title_text": shared_elements.SubmenuTitleText(),
            },
        )
        self.logger = getLogger(__name__)
        self.expected_title = "friends"

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """Check if on the friends list screen via OCR text detection."""
        self.logger.info(f"Checking if app is on the {self.name} screen...")

        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        try:
            # Extract title region and save for OCR
            title_element = self.elements["submenu_title_text"]
            cropped_imgs = pymordial_controller.revomon.extract_regions(
                pymordial_elements=[title_element],
                image=pymordial_screenshot,
            )

            # Read text from extracted region
            result = pymordial_controller.read_text(
                cropped_imgs[0],
                case_sensitive=False,
                strategy=RevomonTextStrategy(),
            )

            # DEBUG: Log what OCR reads
            self.logger.debug(f"OCR result for {self.name}: {result}")

            # Check if expected title is in OCR results
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
