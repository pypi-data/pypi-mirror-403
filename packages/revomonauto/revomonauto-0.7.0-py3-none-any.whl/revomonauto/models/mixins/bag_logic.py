"""
Bag logic mixin for RevomonApp.

Handles all bag navigation and tab switching logic.
"""

import time

# Defined Tab Order (Clicking Right Arrow)
BAG_TABS = ["misc", "medicines", "orbs", "capsules", "fruits", "battle"]


class BagLogicMixin:
    """Mixin providing all bag-related logic for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.game_state
    - self.current_bag_tab
    - self._click_with_fallback()
    """

    def go_to_bag_tab(self, target_tab_name: str) -> None:
        """
        Navigates to the specific bag tab using the shortest path.
        Updates self.revomon.current_bag_tab accordingly.
        """
        self.logger.info(f"Navigating to {target_tab_name.title()} tab...")
        self.logger.info(f"Current tab: {self.revomon.current_bag_tab.title()}")
        all_tabs = BAG_TABS

        if target_tab_name not in all_tabs:
            self.logger.error(f"Invalid tab requested: {target_tab_name.title()}")
            return

        if self.revomon.current_bag_tab == target_tab_name:
            self.logger.info(f"Already on {target_tab_name.title()} tab.")
            return

        current_idx = all_tabs.index(self.revomon.current_bag_tab)
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
            button = self.revomon.screens["battle"].elements[
                "change_bag_tab_right_button"
            ]
            direction = "right"
        else:
            clicks = left_dist
            button = self.revomon.screens["battle"].elements[
                "change_bag_tab_left_button"
            ]
            direction = "left"

        self.logger.info(
            f"Switching tab from {self.revomon.current_bag_tab.title()} to {target_tab_name.title()}. ({clicks} clicks {direction})..."
        )

        for _ in range(clicks):
            self.logger.info(f"Clicking {direction} arrow...")
            self.logger.info(f"Current tab: {self.revomon.current_bag_tab.title()}")
            self._click_with_fallback(button)
            # Small delay to let the UI update between tab switches
            time.sleep(0.3)

            # Update internal state
            if direction == "right":
                current_idx = (current_idx + 1) % total_tabs
            else:  # direction == "left"
                current_idx = (current_idx - 1 + total_tabs) % total_tabs
            self.revomon.current_bag_tab = all_tabs[current_idx]
            self.revomon.current_bag_page = 1
            self.logger.info(f"Switched to {self.revomon.current_bag_tab.title()} tab.")
