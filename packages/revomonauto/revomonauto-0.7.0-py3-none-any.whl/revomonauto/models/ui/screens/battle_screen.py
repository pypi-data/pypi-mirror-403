from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import battle_elements, team_bag_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class BattleScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="battle",
            elements={
                "run_button": battle_elements.run_button,
                "run_button_pixel": battle_elements.run_button_pixel,
                "run_confirm_button_pixel": battle_elements.run_confirm_button_pixel,
                "team_bag_battle_button": battle_elements.team_bag_battle_button,
                "team_bag_battle_pixel": battle_elements.team_bag_battle_pixel,
                "attacks_button": battle_elements.attacks_button,
                "attacks_button_pixel": battle_elements.attacks_button_pixel,
                "exit_attacks_button": battle_elements.exit_attacks_button,
                "exit_attacks_button_pixel": battle_elements.exit_attacks_button_pixel,
                "player1_mon_name_text": battle_elements.player1_mon_name_text,
                "player1_mon_nameplate_pixel": battle_elements.player1_mon_nameplate_pixel,
                "player1_mon_lvl_text": battle_elements.player1_mon_lvl_text,
                "player1_mon_hp_img": battle_elements.player1_mon_hp_img,
                "player1_mon_move1_button": battle_elements.player1_mon_move1_button,
                "player1_mon_move2_button": battle_elements.player1_mon_move2_button,
                "player1_mon_move3_button": battle_elements.player1_mon_move3_button,
                "player1_mon_move4_button": battle_elements.player1_mon_move4_button,
                "player2_mon_name_text": battle_elements.player2_mon_name_text,
                "player2_mon_nameplate_pixel": battle_elements.player2_mon_nameplate_pixel,
                "player2_mon_lvl_text": battle_elements.player2_mon_lvl_text,
                "player2_mon_hp_img": battle_elements.player2_mon_hp_img,
                "waiting_for_opponent_text": battle_elements.waiting_for_opponent_text,
                "battle_log_image": battle_elements.battle_log_image,
                # --- Shared Bag Elements (Instantiating Classes) ---
                "change_bag_tab_left_button": team_bag_elements.ChangeBagTabLeftButton(),
                "change_bag_tab_right_button": team_bag_elements.ChangeBagTabRightButton(),
                "bag_item_slot_1": team_bag_elements.BagItemSlot1(),
                "bag_item_slot_2": team_bag_elements.BagItemSlot2(),
                "bag_item_slot_3": team_bag_elements.BagItemSlot3(),
                "bag_use_item_button": team_bag_elements.BagUseItemButton(),
                "bag_confirm_yes_button": team_bag_elements.BagConfirmYesButton(),
            },
        )
        self.logger: Logger = getLogger(__name__)

    def is_current_screen(
        self,
        pymordial_controller: "PymordialController",
        phase: str = None,
    ) -> bool:
        self.logger.info("Checking if app is on the battle screen...")
        try:
            pymordial_screenshot = pymordial_controller.capture_screen()
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            return False

        try:
            if phase is None:
                player1_mon_nameplate_pixel = self.elements[
                    "player1_mon_nameplate_pixel"
                ]
                player2_mon_nameplate_pixel = self.elements[
                    "player2_mon_nameplate_pixel"
                ]
                result = all(
                    [
                        pymordial_controller.is_element_visible(
                            pymordial_element=player1_mon_nameplate_pixel,
                            pymordial_screenshot=pymordial_screenshot,
                        ),
                        pymordial_controller.is_element_visible(
                            pymordial_element=player2_mon_nameplate_pixel,
                            pymordial_screenshot=pymordial_screenshot,
                        ),
                    ]
                )
            elif phase == "attacks_menu":
                exit_attacks_button_pixel = self.elements["exit_attacks_button_pixel"]
                result = pymordial_controller.is_element_visible(
                    pymordial_element=exit_attacks_button_pixel,
                    pymordial_screenshot=pymordial_screenshot,
                )
            elif phase == "team_bag":
                team_bag_battle_pixel = self.elements["team_bag_battle_pixel"]
                result = pymordial_controller.is_element_visible(
                    pymordial_element=team_bag_battle_pixel,
                    pymordial_screenshot=pymordial_screenshot,
                )
            elif phase == "run":
                run_button_pixel = self.elements["run_button_pixel"]
                result = pymordial_controller.is_element_visible(
                    pymordial_element=run_button_pixel,
                    pymordial_screenshot=pymordial_screenshot,
                )
            elif phase == "waiting_for_opponent":
                waiting_for_opponent_text = self.elements["waiting_for_opponent_text"]
                result = pymordial_controller.is_element_visible(
                    pymordial_element=waiting_for_opponent_text,
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
