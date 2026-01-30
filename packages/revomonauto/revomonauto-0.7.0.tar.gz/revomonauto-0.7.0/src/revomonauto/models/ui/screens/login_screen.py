from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import login_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class LoginScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="login",
            elements={
                "login_button": login_elements.LoginButton(),
                "relogin_button": login_elements.ReloginButton(),
                "login_pixel": login_elements.LoginPixel(),
                "disconnect_button": login_elements.DisconnectButton(),
                "disconnect_pixel": login_elements.DisconnectPixel(),
                "server_select_pixel": login_elements.ServerSelectPixel(),
                "revomon_badge_pixel": login_elements.RevomonBadgePixel(),
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(
        self,
        pymordial_controller: "PymordialController",
    ) -> bool:
        """
        Checks if the Revomon app is on the login screen.
        Args:
            pymordial_controller (PymordialController): The PymordialController instance.

        Returns:
            bool: True if the app is on the login screen, False otherwise.
        """
        # Login Screen Scene
        self.logger.info("Checking if app is on the login screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        login_pixel = self.elements["login_pixel"]
        disconnect_pixel = self.elements["disconnect_pixel"]
        server_select_pixel = self.elements["server_select_pixel"]
        revomon_badge_pixel = self.elements["revomon_badge_pixel"]

        # Convert to bytes for consistency (is_element_visible expects bytes | None)
        screenshot_bytes: bytes | None = None
        try:
            import io

            from numpy import ndarray
            from PIL import Image

            if isinstance(pymordial_screenshot, ndarray):
                buf = io.BytesIO()
                Image.fromarray(pymordial_screenshot).save(buf, format="PNG")
                screenshot_bytes = buf.getvalue()
            elif isinstance(pymordial_screenshot, bytes):
                screenshot_bytes = pymordial_screenshot
        except Exception:
            if isinstance(pymordial_screenshot, bytes):
                screenshot_bytes = pymordial_screenshot

        try:
            result = all(
                [
                    pymordial_controller.is_element_visible(
                        pymordial_element=login_pixel,
                        pymordial_screenshot=screenshot_bytes,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=disconnect_pixel,
                        pymordial_screenshot=screenshot_bytes,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=server_select_pixel,
                        pymordial_screenshot=screenshot_bytes,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=revomon_badge_pixel,
                        pymordial_screenshot=screenshot_bytes,
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
