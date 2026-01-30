from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import main_menu_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class MainMenuScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="main_menu",
            elements={
                "tamer_name_text": main_menu_elements.TamerNameText(),
                "tamer_selfie_img": main_menu_elements.TamerSelfieImg(),
                "wardrobe_button": main_menu_elements.WardrobeButton(),
                "team_bag_menu_button": main_menu_elements.TeamBagMenuButton(),
                "recall_button": main_menu_elements.RecallButton(),
                "friends_button": main_menu_elements.FriendsButton(),
                "settings_button": main_menu_elements.SettingsButton(),
                "revodex_button": main_menu_elements.RevodexButton(),
                "market_button": main_menu_elements.MarketButton(),
                "discussion_button": main_menu_elements.DiscussionButton(),
                "pvp_button": main_menu_elements.PvpButton(),
                "clan_button": main_menu_elements.ClanButton(),
                "reset_position_button": main_menu_elements.ResetPositionButton(),
                "quit_game_button": main_menu_elements.QuitGameButton(),
                "quit_game_pixel": main_menu_elements.QuitGamePixel(),
                # PVP Queue loading circle pixels
                "pvp_loading_pixel_top": main_menu_elements.PvpLoadingPixelTop(),
                "pvp_loading_pixel_right": main_menu_elements.PvpLoadingPixelRight(),
                "pvp_loading_pixel_bottom": main_menu_elements.PvpLoadingPixelBottom(),
                "pvp_loading_pixel_left": main_menu_elements.PvpLoadingPixelLeft(),
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(
        self,
        pymordial_controller: "PymordialController",
        pymordial_screenshot: bytes | None = None,
    ) -> bool:
        """
        Checks if the Revomon app is on the main menu screen.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.
            pymordial_screenshot (bytes | None, optional): Screenshot of the app. Defaults to None.

        Returns:
            bool: True if the app is on the main menu screen, False otherwise.
        """
        # Main Menu Screen Scene
        self.logger.info("Checking if app is on the main menu screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        quit_game_pixel = self.elements["quit_game_pixel"]

        try:
            result = pymordial_controller.is_element_visible(
                pymordial_element=quit_game_pixel,
                pymordial_screenshot=pymordial_screenshot,
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
