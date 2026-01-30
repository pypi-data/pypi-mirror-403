from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import team_bag_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class TeamBagScreen(PymordialScreen):
    """Team Bag Screen for Revomon app."""

    def __init__(self):
        super().__init__(
            name="team_bag",
            elements={
                "change_bag_tab_left_button": team_bag_elements.ChangeBagTabLeftButton(),
                "change_bag_tab_left_pixel": team_bag_elements.ChangeBagTabLeftPixel(),
                "change_bag_tab_right_button": team_bag_elements.ChangeBagTabRightButton(),
                "change_bag_tab_right_pixel": team_bag_elements.ChangeBagTabRightPixel(),
                "remove_from_team_button": team_bag_elements.RemoveFromTeamButton(),
                "remove_from_team_pixel": team_bag_elements.RemoveFromTeamPixel(),
                "remove_item_button": team_bag_elements.RemoveItemButton(),
                "remove_item_pixel": team_bag_elements.RemoveItemPixel(),
                "set_first_button": team_bag_elements.SetFirstButton(),
                "set_first_pixel": team_bag_elements.SetFirstPixel(),
                "send_to_battle_button": team_bag_elements.SendToBattleButton(),
                "send_to_battle_pixel": team_bag_elements.SendToBattlePixel(),
                "no_item_equipped_pixel": team_bag_elements.NoItemEquippedPixel(),
                # --- Shared Bag Elements ---
                "bag_item_slot_1": team_bag_elements.BagItemSlot1(),
                "bag_item_slot_2": team_bag_elements.BagItemSlot2(),
                "bag_item_slot_3": team_bag_elements.BagItemSlot3(),
                "bag_use_item_button": team_bag_elements.BagUseItemButton(),
                "bag_give_item_button": team_bag_elements.BagGiveItemButton(),
                "bag_confirm_yes_button": team_bag_elements.BagConfirmYesButton(),
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(self, pymordial_controller: "PymordialController") -> bool:
        """
        Checks if the Revomon app is on the team bag screen.

        Args:
            pymordial_controller (PymordialController): Pymordial controller instance.

        Returns:
            bool: True if the app is on the team bag screen, False otherwise.
        """
        self.logger.info("Checking if app is on the team bag screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        change_bag_tab_left_pixel = self.elements["change_bag_tab_left_pixel"]
        change_bag_tab_right_pixel = self.elements["change_bag_tab_right_pixel"]
        try:
            result = all(
                [
                    pymordial_controller.is_element_visible(
                        pymordial_element=change_bag_tab_left_pixel,
                        pymordial_screenshot=pymordial_screenshot,
                    ),
                    pymordial_controller.is_element_visible(
                        pymordial_element=change_bag_tab_right_pixel,
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
            f"CURRENTLY ON the {self.name} screen."
            if result
            else f"NOT ON the {self.name} screen."
        )
        return result
