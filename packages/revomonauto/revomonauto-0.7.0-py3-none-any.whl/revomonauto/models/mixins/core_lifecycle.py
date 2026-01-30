"""
Core lifecycle mixin for RevomonApp.

Handles app startup, shutdown, login, state detection, and global state management.
"""

from pymordial import AppState

from ..action import action
from ..states import BattleState, GameState, requires_state
from ..strategies import RevomonTextStrategy

# Game Config
DEFAULT_BAG_TAB = "misc"


class CoreLifecycleMixin:
    """Mixin providing core lifecycle and state management for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.app_state
    - self.game_state
    - self.battle_sub_state
    - self.curr_screen
    - self.navigator
    """

    def _click_with_fallback(self, element, times=1) -> None:
        """
        Attempts to click an element via image detection.
        If detection fails, falls back to clicking the static coordinates.
        """
        self.logger.info(f"Attempting to click element '{element.label}'...")
        if self.is_element_visible(element):
            self.logger.info(f"Element '{element.label}' found via image. Clicking...")
            self.click_element(element, times=times)
        else:
            self.logger.warning(
                f"Element '{element.label}' not visible. Falling back to coordinates."
            )
            if element.center:
                self.click_coord(element.center, times=times)
            else:
                self.logger.error(
                    f"Element '{element.label}' has no coordinates defined!"
                )

    def get_current_state(self) -> dict:
        return {
            "current_screen": self.revomon.curr_screen,
            "tv_current_page": self.revomon.tv_current_page,
            "tv_slot_selceted": self.revomon.tv_slot_selected,
            "tv_searching_for": self.revomon.tv_searching_for,
            "current_city": self.revomon.current_city,
            "current_location": self.revomon.current_location,
            "current_bag_tab": self.revomon.current_bag_tab,
            "bluestacks_state": self.bluestacks.state.current_state,
            "app_state": self.revomon.app_state.current_state,
            "game_state": self.revomon.game_state,
            "battle_sub_state": self.revomon.battle_sub_state,
        }

    def get_current_time_cycle(
        self,
        screenshot: bytes | None = None,
    ) -> str:
        """Detect current in-game time cycle.

        Args:
            screenshot: Optional pre-captured screenshot bytes.

        Returns:
            'morning', 'afternoon', 'night', or 'unknown'.
        """
        from pymordial import PymordialPixel

        # Time cycle detection pixels
        morning_pixel = PymordialPixel(
            label="time_morning",
            og_resolution=(1920, 1080),
            position=(1850, 55),
            pixel_color=(251, 204, 65),
            tolerance=15,
        )
        afternoon_pixel = PymordialPixel(
            label="time_afternoon",
            og_resolution=(1920, 1080),
            position=(1875, 30),
            pixel_color=(255, 244, 91),
            tolerance=15,
        )
        night_pixel = PymordialPixel(
            label="time_night",
            og_resolution=(1920, 1080),
            position=(1875, 30),
            pixel_color=(255, 249, 192),
            tolerance=15,
        )

        if screenshot is None:
            screenshot = self.capture_screen()

        # Check morning first (different position)
        if self.ui.check_pixel_color(morning_pixel, screenshot):
            return "morning"

        # Check afternoon/night (same position, different colors)
        if self.ui.check_pixel_color(afternoon_pixel, screenshot):
            return "afternoon"

        if self.ui.check_pixel_color(night_pixel, screenshot):
            return "night"

        return "unknown"

    @action
    def open_revomon_app(self) -> None:
        match self.revomon.app_state.current_state:
            case AppState.CLOSED:
                self.open_app(
                    app_name=self.revomon.app_name,
                    package_name=self.revomon.package_name,
                )

    @action
    def close_revomon_app(self) -> None:
        # Force reconnect ADB before closing - is_connected() doesn't detect stale connections
        # that have been idle for a while (e.g., after "Press Enter" pause)
        self.logger.info("Refreshing ADB connection before close...")
        self.adb.connect()

        match self.revomon.app_state.current_state:
            case AppState.READY | AppState.LOADING:
                self.close_app(
                    app_name=self.revomon.app_name,
                    package_name=self.revomon.package_name,
                )

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def quit_game(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            quit_game_button = self.revomon.screens["main_menu"].elements[
                "quit_game_button"
            ]
            self._click_with_fallback(quit_game_button)

    @requires_state(GameState.NOT_STARTED)
    @action
    def start_game(self) -> None:
        start_btn = self.revomon.screens["start_game"].elements["start_game_button"]
        self._click_with_fallback(start_btn)

    @requires_state(GameState.STARTED)
    @action
    def login(self) -> None:
        login_btn = self.revomon.screens["login"].elements["login_button"]
        relogin_btn = self.revomon.screens["login"].elements["relogin_button"]

        if self.is_element_visible(relogin_btn):
            self.click_element(relogin_btn)
            self.revomon.current_bag_tab = DEFAULT_BAG_TAB  # Reset Bag State
            self.logger.info("Relogin button clicked.")
            return
        elif self.is_element_visible(login_btn):
            self.click_element(login_btn)
            self.revomon.current_bag_tab = DEFAULT_BAG_TAB  # Reset Bag State
            self.logger.info("Login button clicked.")
            return

        self.logger.warning(
            "Login buttons not found via image. Falling back to Login button coordinates."
        )
        if login_btn.center:
            self.click_coord(login_btn.center)
            self.revomon.current_bag_tab = DEFAULT_BAG_TAB  # Reset Bag State

    def update_world_state(
        self,
        new_app_state: AppState | None = None,
        new_game_state: GameState | None = None,
        new_battle_sub_state: BattleState | None = None,
        ignore_state_change_validation: bool = False,
    ) -> None:

        if new_app_state and self.revomon.app_state.current_state != new_app_state:
            self.revomon.app_state.transition_to(
                new_app_state, ignore_validation=ignore_state_change_validation
            )
            self.logger.info(f"App state updated to: {new_app_state}")

        if new_game_state and self.revomon.game_state != new_game_state:
            self.revomon.game_state = new_game_state
            self.logger.info(f"Game state updated to: {new_game_state}")

        if (
            new_battle_sub_state
            and self.revomon.battle_sub_state != new_battle_sub_state
        ):
            self.revomon.battle_sub_state = new_battle_sub_state
            self.logger.info(f"Battle sub-state updated to: {new_battle_sub_state}")

        if not any([new_app_state, new_game_state, new_battle_sub_state]):
            self.logger.info("No state changes provided.")
            self.logger.info("Scanning for current screen...")

            # Helper to safely check screens
            def safe_check(check_func, **kwargs):
                try:
                    return check_func(**kwargs)
                except Exception as e:
                    self.logger.warning(
                        f"Screen check failed for {check_func.__name__}: {e}"
                    )
                    return False

            if any(
                [
                    safe_check(
                        self.is_start_game_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_login_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_overworld_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_tv_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_team_bag_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_main_menu_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_on_battle_screen,
                        ignore_state_change_validation=True,
                    ),
                    safe_check(
                        self.is_attacks_menu_screen,
                        ignore_state_change_validation=True,
                    ),
                ]
            ):
                self.logger.info("Current screen detected. World state updated.")
                self.logger.info(f"Detected screen: {self.revomon.curr_screen}")
            else:
                self.logger.info("New World State initialized.")

    def is_start_game_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["start_game"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.NOT_STARTED,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "start_game"
                self.start_streaming()
                return True
            case _:
                return False

    def is_login_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["login"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.STARTED,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "login"
                return True
            case _:
                return False

    def is_overworld_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["overworld"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.OVERWORLD,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "overworld"

                # Initialize navigator on first detection of overworld (after login)
                if not self.navigator:
                    from ..navigator import Navigator

                    self.navigator = Navigator(self)
                    self.logger.info("Navigator initialized after login")

                return True
            case _:
                return False

    def is_tv_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        try:
            match self.revomon.screens["tv"].is_current_screen(
                pymordial_controller=self,
            ):
                case True:
                    self.update_world_state(
                        new_app_state=AppState.READY,
                        new_game_state=GameState.TV,
                        new_battle_sub_state=BattleState.IDLE,
                        ignore_state_change_validation=ignore_state_change_validation,
                    )
                    self.revomon.curr_screen = "tv"
                    return True
                case _:
                    return False
        except Exception as e:
            raise Exception(f"error during 'is_tv_screen': {e}")

    def is_team_bag_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        try:
            match self.revomon.screens["team_bag"].is_current_screen(
                pymordial_controller=self,
            ):
                case True:
                    if self.revomon.game_state == GameState.BATTLE:
                        self.update_world_state(
                            new_app_state=AppState.READY,
                            new_game_state=GameState.BATTLE,
                            new_battle_sub_state=BattleState.BAG_OPEN,
                            ignore_state_change_validation=ignore_state_change_validation,
                        )
                        self.revomon.curr_screen = "battle_bag"
                        return True
                    elif self.revomon.game_state == GameState.MAIN_MENU:
                        self.update_world_state(
                            new_app_state=AppState.READY,
                            new_game_state=GameState.MENU_BAG,
                            new_battle_sub_state=BattleState.IDLE,
                            ignore_state_change_validation=ignore_state_change_validation,
                        )
                        self.revomon.curr_screen = "menu_bag"
                        return True
                case _:
                    return False
        except Exception as e:
            raise Exception(f"error during 'is_team_bag_screen': {e}")

    def is_main_menu_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["main_menu"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.MAIN_MENU,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "main_menu"
                return True
            case _:
                return False

    def get_username(self) -> str | None:
        """Extract player username from main menu title region via OCR.

        The username is displayed in the title region (75, 15) with size (610, 75)
        when on the main menu screen. This is the same region used for submenu titles.

        Returns:
            str | None: The player's username, or None if extraction fails.
        """
        from ..ui.elements import shared_elements

        self.logger.info("Extracting player username...")

        try:
            pymordial_screenshot = self.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return None

        try:
            title_element = shared_elements.SubmenuTitleText()
            cropped_img = self.extract_regions(
                pymordial_elements=[title_element],
                image=pymordial_screenshot,
            )

            result = self.read_text(
                cropped_img[0],
                case_sensitive=False,
                strategy=RevomonTextStrategy(),
            )

            if result and result[0]:
                username = result[0].strip()
                self.logger.info(f"Extracted username: '{username}'")
                return username

            self.logger.warning("No username found in OCR result")
            return None

        except Exception as e:
            self.logger.error(f"Failed to extract username: {e}")
            return None

    def is_pvp_queued(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        """Check if PVP queue is active by detecting loading circle pixels."""
        if self.revomon.screens["pvp_queue"].is_current_screen(self):
            self.update_world_state(
                new_app_state=AppState.READY,
                # Do not force GameState change, preserve current (e.g. OVERWORLD)
                new_battle_sub_state=BattleState.PVP_QUEUE,
                ignore_state_change_validation=ignore_state_change_validation,
            )
            # Do not change curr_screen to pvp_queue, as it's an overlay
            # self.revomon.curr_screen = "pvp_queue"
            return True
        return False

    def is_wardrobe_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["wardrobe"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.WARDROBE,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "wardrobe"
                return True
            case _:
                return False

    def is_friends_list_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["friends_list"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.FRIENDS_LIST,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "friends_list"
                return True
            case _:
                return False

    def is_settings_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["settings"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.SETTINGS,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "settings"
                return True
            case _:
                return False

    def is_revodex_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["revodex"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.REVODEX,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "revodex"
                return True
            case _:
                return False

    def is_market_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["market"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.MARKET,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "market"
                return True
            case _:
                return False

    def is_discussion_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["discussion"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.DISCUSSION,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "discussion"
                return True
            case _:
                return False

    def is_clan_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        match self.revomon.screens["clan"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.CLAN,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "clan"
                return True
            case _:
                return False

    def is_on_battle_screen(
        self,
        ignore_state_change_validation: bool = False,
        extract_battle_info: bool = False,
    ) -> bool:

        match self.revomon.screens["battle"].is_current_screen(
            pymordial_controller=self,
        ):
            case True:
                self.logger.info("Battle screen is open.")
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.BATTLE,
                    new_battle_sub_state=BattleState.IDLE,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "in_battle"

                if extract_battle_info:
                    self._extract_battle_info()
                return True
            case _:
                self.logger.info("Battle screen is not open.")
                return False

    def is_attacks_menu_screen(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        self.logger.info("Checking if attacks menu is open...")
        match self.revomon.screens["battle"].is_current_screen(
            pymordial_controller=self,
            phase="attacks_menu",
        ):
            case True:
                self.logger.info("Attacks menu is open.")
                self.update_world_state(
                    new_app_state=AppState.READY,
                    new_game_state=GameState.BATTLE,
                    new_battle_sub_state=BattleState.ATTACKS_MENU_OPEN,
                    ignore_state_change_validation=ignore_state_change_validation,
                )
                self.revomon.curr_screen = "attacks_menu"
                self.extract_battle_moves()
                return True
            case _:
                self.logger.info("Attacks menu is not open.")
                return False

    def is_waiting_for_opponent(
        self,
        ignore_state_change_validation: bool = False,
    ) -> bool:
        try:
            self.logger.info(
                f"Using {'Streaming' if self.is_streaming else 'Screencap'} to capture screen."
            )
            screenshot_bytes = self.capture_screen()
            waiting_for_opponent_text = self.revomon.screens["battle"].elements[
                "waiting_for_opponent_text"
            ]
            cropped_img = self.extract_regions(
                pymordial_elements=[waiting_for_opponent_text],
                image=screenshot_bytes,
            )
            result = self.read_text(
                cropped_img[0],
                strategy=RevomonTextStrategy(),
            )
            if len(result) > 0:
                for text in result:
                    if "for opponent" in str(text).lower():
                        self.logger.info("Waiting for opponent...")
                        self.update_world_state(
                            new_app_state=AppState.READY,
                            new_game_state=GameState.BATTLE,
                            new_battle_sub_state=BattleState.WAITING_FOR_OPPONENT,
                            ignore_state_change_validation=ignore_state_change_validation,
                        )
                        self.revomon.curr_screen = "battle"
                        return True
            return False
        except Exception as e:
            raise Exception(f"Error setting is_waiting_for_opponent(): {e}")

    def reset(self, auto_update: bool = False) -> None:
        self.revomon.curr_screen = None
        self.revomon.is_mon_recalled = None
        self.revomon.tv_current_page = 1
        self.revomon.tv_searching_for = None
        self.revomon.tv_slot_selected = 0
        self.revomon.tv_slot_selected_attribs = None
        self.revomon.is_grading = False
        self.revomon.is_mons_graded = False
        self.revomon.current_bag_tab = DEFAULT_BAG_TAB
        self.revomon.current_city = None
        self.revomon.current_location = None

        self.mon_details_img = None
        self.mon_detail_imgs = None
