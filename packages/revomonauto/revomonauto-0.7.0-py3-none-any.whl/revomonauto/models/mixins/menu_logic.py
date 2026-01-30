"""
Menu logic mixin for RevomonApp.

Handles all menu open/close operations and menu-related navigation.
"""

import time

from ..action import action
from ..states import GameState, requires_state

LOGGED_IN_STATES = (
    GameState.OVERWORLD,
    GameState.MAIN_MENU,
    GameState.MENU_BAG,
    GameState.WARDROBE,
    GameState.FRIENDS_LIST,
    GameState.SETTINGS,
    GameState.REVODEX,
    GameState.MARKET,
    GameState.DISCUSSION,
    GameState.CLAN,
    GameState.TV,
)

WARDROBE_TABS = ["head", "torso", "legs", "hands", "shoes", "hat"]


class MenuLogicMixin:
    """Mixin providing all menu-related logic for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.game_state
    - self._click_with_fallback()
    """

    # ==================== Main Menu ====================

    @requires_state(GameState.OVERWORLD)
    @action
    def open_main_menu(self) -> None:
        main_menu_btn = self.revomon.screens["overworld"].elements["main_menu_button"]
        self._click_with_fallback(main_menu_btn)
        time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.MAIN_MENU)
    @action
    def close_main_menu(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.OVERWORLD)
    @action
    def reset_position(self) -> None:
        """
        Teleports the player back to their last saved waypoint.
        Way points are saved when passing through portals.
        """
        self.logger.info("Resetting position to last waypoint...")

        # Open main menu
        self.open_main_menu()

        # Click reset position button
        reset_btn = self.revomon.screens["main_menu"].elements["reset_position_button"]
        self._click_with_fallback(reset_btn)
        time.sleep(3)  # Wait for teleport animation

        self.close_main_menu()

        self.logger.info("Position reset to last waypoint")

    # ==================== Bag ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_menu_bag(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            team_bag_btn = self.revomon.screens["main_menu"].elements[
                "team_bag_menu_button"
            ]
            self._click_with_fallback(team_bag_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.MENU_BAG)
    @action
    def close_menu_bag(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Wardrobe ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_wardrobe(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            wardrobe_btn = self.revomon.screens["main_menu"].elements["wardrobe_button"]
            self._click_with_fallback(wardrobe_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.WARDROBE)
    @action
    def go_to_wardrobe_tab(self, target_tab_name: str) -> None:
        """
        Navigates to the specific wardrobe tab using the shortest path.
        Updates self.revomon.current_wardrobe_tab accordingly.
        """
        self.logger.info(f"Navigating to {target_tab_name.title()} tab...")
        self.logger.info(f"Current tab: {self.revomon.current_wardrobe_tab.title()}")
        all_tabs = WARDROBE_TABS

        if target_tab_name not in all_tabs:
            self.logger.error(f"Invalid tab requested: {target_tab_name.title()}")
            return

        if self.revomon.current_wardrobe_tab == target_tab_name:
            self.logger.info(f"Already on {target_tab_name.title()} tab.")
            return

        current_idx = all_tabs.index(self.revomon.current_wardrobe_tab)
        target_idx = all_tabs.index(target_tab_name)
        total_tabs = len(all_tabs)

        # Calculate distances
        # Clockwise (Right Button)
        right_dist = (target_idx - current_idx) % total_tabs
        # Counter-Clockwise (Left Button)
        left_dist = (current_idx - target_idx) % total_tabs

        # Choose shortest path
        if right_dist <= left_dist:
            clicks = right_dist
            direction = "right"
        else:
            clicks = left_dist
            direction = "left"

        change_tab_btn = self.revomon.screens["wardrobe"].elements[
            f"change_wardrobe_tab_{direction}_pixel"
        ]

        self.logger.info(
            f"Switching tab from {self.revomon.current_wardrobe_tab.title()} to {target_tab_name.title()}. ({clicks} clicks {direction})..."
        )

        for _ in range(clicks):
            self.logger.info(f"Clicking {direction} arrow...")

            self._click_with_fallback(change_tab_btn)
            # Small delay to let the UI update between tab switches
            time.sleep(0.3)
            # Update internal state
            if direction == "right":
                current_idx = (current_idx + 1) % total_tabs
            else:  # direction == "left"
                current_idx = (current_idx - 1 + total_tabs) % total_tabs
            self.revomon.current_wardrobe_tab = all_tabs[current_idx]
            self.revomon.current_wardrobe_page = 1
            self.logger.info(
                f"Switched to {self.revomon.current_wardrobe_tab.title()} tab."
            )

    @requires_state(GameState.WARDROBE)
    @action
    def close_wardrobe(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Recall Revomon ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def recall_revomon(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            recall_btn = self.revomon.screens["main_menu"].elements["recall_button"]
            self._click_with_fallback(recall_btn)

    # ==================== Friends List ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_friends_list(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            friends_btn = self.revomon.screens["main_menu"].elements["friends_button"]
            self._click_with_fallback(friends_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.FRIENDS_LIST)
    @action
    def close_friends_list(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Settings ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_settings(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            settings_btn = self.revomon.screens["main_menu"].elements["settings_button"]
            self._click_with_fallback(settings_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.SETTINGS)
    @action
    def close_settings(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Revodex ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_revodex(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            revodex_btn = self.revomon.screens["main_menu"].elements["revodex_button"]
            self._click_with_fallback(revodex_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.REVODEX)
    @action
    def close_revodex(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Market ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_market(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            market_btn = self.revomon.screens["main_menu"].elements["market_button"]
            self._click_with_fallback(market_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.MARKET)
    @action
    def close_market(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Discussion ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_discussion(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            discussion_btn = self.revomon.screens["main_menu"].elements[
                "discussion_button"
            ]
            self._click_with_fallback(discussion_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.DISCUSSION)
    @action
    def close_discussion(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== Clan ====================

    @requires_state(GameState.OVERWORLD, GameState.MAIN_MENU)
    @action
    def open_clan(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        if self.revomon.game_state == GameState.MAIN_MENU:
            clan_btn = self.revomon.screens["main_menu"].elements["clan_button"]
            self._click_with_fallback(clan_btn)
            time.sleep(1)  # Wait for menu animation

    @requires_state(GameState.CLAN)
    @action
    def close_clan(self) -> None:
        exit_btn = self.revomon.screens["shared"].elements["exit_menu_button"]
        self._click_with_fallback(exit_btn)
        time.sleep(1)  # Wait for menu animation

    # ==================== PVP Queue ====================

    @requires_state(GameState.MAIN_MENU, GameState.OVERWORLD)
    @action
    def enter_pvp_queue(self) -> None:
        if self.revomon.game_state == GameState.OVERWORLD:
            self.open_main_menu()
        pvp_btn = self.revomon.screens["main_menu"].elements["pvp_button"]
        self._click_with_fallback(pvp_btn)

    @requires_state(GameState.MAIN_MENU)
    @action
    def exit_pvp_queue(self) -> None:
        pvp_btn = self.revomon.screens["main_menu"].elements["pvp_button"]
        self._click_with_fallback(pvp_btn)
