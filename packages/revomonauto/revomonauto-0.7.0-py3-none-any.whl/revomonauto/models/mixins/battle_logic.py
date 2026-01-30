"""
Battle logic mixin for RevomonApp.

Handles all battle-related operations including moves, bag usage, and running.
"""

import io
import re
import time
from typing import Optional

import numpy as np
from PIL import Image
from pymordial import PymordialElement

from ..action import action
from ..states import BattleState, GameState, requires_state
from ..strategies import BattleStrategy, RandomMove, RevomonTextStrategy

HEALTH_BAR_DARK_THRESHOLD = 50
MAX_LEVEL = 100

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


class BattleLogicMixin:
    """Mixin providing all battle-related logic for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.game_state
    - self.battle_sub_state
    - self.auto_run
    - self.auto_battle
    - self.mon_on_field
    - self.opps_mon_on_field
    - self._click_with_fallback()
    - self.go_to_bag_tab()
    """

    def extract_regions(
        self,
        pymordial_elements: list[PymordialElement],
        image: bytes | str | np.ndarray,
    ) -> list[np.ndarray]:

        if isinstance(image, np.ndarray):
            # Convert numpy array (BGR from OpenCV) to PIL Image
            image = Image.fromarray(image)
        elif isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        else:
            image = Image.open(image)
        cropped_imgs = []

        for pymordial_element in pymordial_elements:
            # Calculate region boundaries
            left = pymordial_element.position[0]
            top = pymordial_element.position[1]
            right = left + pymordial_element.size[0]
            bottom = top + pymordial_element.size[1]

            # Extract the region
            cropped_img = image.crop((left, top, right, bottom))
            cropped_imgs.append(np.array(cropped_img))

        return cropped_imgs

    def extract_health_percentage(
        self, image_input: str | bytes | np.ndarray, padding: int = 5
    ) -> float:
        try:
            if isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
                img_array = np.array(img.convert("RGB"))
            elif isinstance(image_input, str):
                with Image.open(image_input) as img:
                    img_array = np.array(img.convert("RGB"))
            elif isinstance(image_input, np.ndarray):
                img_array = image_input
            else:
                self.logger.error(f"Unsupported image type: {type(image_input)}")
                return -1.0

            height, width, _ = img_array.shape
            y_scan = height // 2

            if width <= 2 * padding:
                self.logger.error(
                    "Error: Image width is too small to account for padding."
                )
                return -1.0

            # Direct numpy slicing for the scan line
            # shape of scan_line is (width, 3)
            scan_line = img_array[y_scan, padding : width - padding]

            # Vectorized check: all channels < threshold
            # missing_health_mask is a boolean array
            missing_health_mask = np.all(scan_line < HEALTH_BAR_DARK_THRESHOLD, axis=1)

            missing_health_pixels = np.sum(missing_health_mask)
            total_pixels = scan_line.shape[0]

            if total_pixels == 0:
                return 0.0

            health_pixels = total_pixels - missing_health_pixels
            health_percentage = (health_pixels / total_pixels) * 100

            return health_percentage

        except FileNotFoundError:
            self.logger.error(f"Error: The file at {image_input} was not found.")
            return -1.0
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            return -1.0

    def _extract_battle_info(self):
        self.logger.info("Extracting battle info...")
        try:
            self.logger.info(
                f"Using {'Streaming' if self.adb.is_streaming else 'Screencap'} to capture screen."
            )
            screenshot_bytes = self.capture_screen()
            if screenshot_bytes is None:
                raise Exception("Failed to take screenshot")

            # Element definitions shortened for brevity, logic remains
            player1_mon_name_text = self.revomon.screens["battle"].elements[
                "player1_mon_name_text"
            ]
            player1_mon_lvl_text = self.revomon.screens["battle"].elements[
                "player1_mon_lvl_text"
            ]
            player1_mon_hp_img = self.revomon.screens["battle"].elements[
                "player1_mon_hp_img"
            ]
            player2_mon_name_text = self.revomon.screens["battle"].elements[
                "player2_mon_name_text"
            ]
            player2_mon_lvl_text = self.revomon.screens["battle"].elements[
                "player2_mon_lvl_text"
            ]
            player2_mon_hp_img = self.revomon.screens["battle"].elements[
                "player2_mon_hp_img"
            ]

            cropped_imgs = self.extract_regions(
                pymordial_elements=[
                    player1_mon_name_text,
                    player1_mon_lvl_text,
                    player1_mon_hp_img,
                    player2_mon_name_text,
                    player2_mon_lvl_text,
                    player2_mon_hp_img,
                ],
                image=screenshot_bytes,
            )

            mon_name = self.read_text(cropped_imgs[0], strategy=RevomonTextStrategy())
            if mon_name and mon_name[0]:
                self.revomon.mon_on_field["name"] = mon_name[0]

            mon_lvl = self.read_text(
                cropped_imgs[1],
                strategy=RevomonTextStrategy(mode="level"),
            )
            if len(mon_lvl) == 1:
                mon_lvl = mon_lvl[0]
                if mon_lvl.isdigit():
                    self.revomon.mon_on_field["level"] = (
                        MAX_LEVEL if int(mon_lvl) > MAX_LEVEL else int(mon_lvl)
                    )

            mon_hp = self.extract_health_percentage(cropped_imgs[2])
            if mon_hp:
                self.revomon.mon_on_field["current_hp_percentage"] = float(
                    f"{mon_hp:.2f}"
                )

            opps_mon_name = self.read_text(
                cropped_imgs[3], strategy=RevomonTextStrategy()
            )
            if opps_mon_name and opps_mon_name[0]:
                self.revomon.opps_mon_on_field["name"] = opps_mon_name[0]

            opps_mon_lvl = self.read_text(
                cropped_imgs[4],
                strategy=RevomonTextStrategy(mode="level"),
            )
            if len(opps_mon_lvl) == 1:
                opps_mon_lvl = opps_mon_lvl[0]
                if opps_mon_lvl.isdigit():
                    self.revomon.opps_mon_on_field["level"] = (
                        MAX_LEVEL
                        if int(opps_mon_lvl) > MAX_LEVEL
                        else int(opps_mon_lvl)
                    )

            opps_mon_hp = self.extract_health_percentage(cropped_imgs[5])
            if opps_mon_hp:
                self.revomon.opps_mon_on_field["current_hp_percentage"] = float(
                    f"{opps_mon_hp:.2f}"
                )

            self.logger.info("Initial battle info extracted successfully")
        except Exception as e:
            self.logger.error(f"Error extracting initial battle info: {e}")

    def extract_battle_moves(self):
        def process_move_data(move_data: list[str]):
            try:
                # Improved Regex Processing (No OpenCV needed)
                full_text = " ".join(move_data).lower()
                # Fix common OCR mixups in PP
                full_text = re.sub(r"(\d+)h(\d+)", r"\1/\2", full_text)  # h -> /
                full_text = re.sub(r"(\d+)i(\d+)", r"\1/\2", full_text)  # i -> /
                full_text = re.sub(r"(\d+)o(\d+)", r"\1/\2", full_text)  # o -> /

                # Match "move name 15/25" pattern
                match = re.search(r"(.*?)\s+(\d+/\d+)", full_text)

                if match:
                    name = match.group(1).strip()
                    pp_str = match.group(2)

                    # Clean up common name typos
                    name = name.replace("pouder", "powder")
                    name = name.replace("uhip", "whip")
                    name = name.replace("toh1o", "seed")

                    return [name, pp_str]

                # Fallback to old logic if regex fails
                if len(move_data) < 2:
                    return move_data

                return move_data[:2]

            except Exception as e:
                self.logger.error(f"Error processing move data: {e}")
                return None

        try:
            self.logger.info("Extracting battle moves...")
            self.logger.info(
                f"Using {'Streaming' if self.adb.is_streaming else 'Screencap'} to capture screen."
            )
            screenshot_bytes = self.capture_screen()
            if screenshot_bytes is None:
                raise Exception("Failed to take screenshot")

            move_ui_elements = [
                self.revomon.screens["battle"].elements["player1_mon_move1_button"],
                self.revomon.screens["battle"].elements["player1_mon_move2_button"],
                self.revomon.screens["battle"].elements["player1_mon_move3_button"],
                self.revomon.screens["battle"].elements["player1_mon_move4_button"],
            ]

            self.logger.info("Extracting Moves regions...")
            cropped_imgs = self.extract_regions(
                pymordial_elements=move_ui_elements,
                image=screenshot_bytes,
            )

            for i, move_ui in enumerate(move_ui_elements):
                processed_move_data = self.read_text(
                    cropped_imgs[i], strategy=RevomonTextStrategy(mode="move")
                )
                if not processed_move_data:
                    continue
                self.logger.info(f"-------->{processed_move_data}<--------")

                # Update Name if present
                if len(processed_move_data) >= 1:
                    self.revomon.mon_on_field["moves"][i]["name"] = processed_move_data[
                        0
                    ]

                # Update PP if present and valid
                if len(processed_move_data) >= 2:
                    try:
                        pp_parts = processed_move_data[1].split("/")
                        if len(pp_parts) == 2:
                            self.revomon.mon_on_field["moves"][i]["pp"]["current"] = (
                                int(pp_parts[0])
                            )
                            self.revomon.mon_on_field["moves"][i]["pp"]["total"] = int(
                                pp_parts[1]
                            )
                    except (ValueError, IndexError) as e:
                        self.logger.error(
                            f"Error parsing PP for move {i+1}: {processed_move_data[1]} - {e}"
                        )
                        # Don't fail completely, just leave PP as None/stale

            self.logger.info("Current battle moves info extracted successfully")
        except Exception as e:
            self.logger.error(f"Error extracting current battle moves info: {e}")

    def extract_battle_log(self):
        try:
            self.logger.info(
                f"Using {'Streaming' if self.adb.is_streaming else 'Screencap'} to capture screen."
            )
            screenshot_bytes = self.capture_screen()
            if screenshot_bytes is None:
                raise Exception("Failed to take screenshot")

            if self.is_main_menu_screen():
                self.logger.info("Closing main menu...")
                self.close_main_menu()
                self.logger.info("Battle over...")

            battle_log_image = self.revomon.screens["battle"].elements[
                "battle_log_image"
            ]
            cropped_img = self.extract_regions(
                pymordial_elements=[
                    battle_log_image,
                ],
                image=screenshot_bytes,
            )
            battle_log = self.read_text(cropped_img[0], strategy=RevomonTextStrategy())
            if battle_log:
                self.logger.info(f"Battle log: {battle_log}")
        except Exception as e:
            self.logger.error(f"Error extracting battle log region: {e}")

    @requires_state(GameState.BATTLE)
    @action
    def open_attacks_menu(self) -> None:
        self.logger.info("Opening attacks menu...")
        attacks_btn = self.revomon.screens["battle"].elements["attacks_button"]
        self._click_with_fallback(attacks_btn)

    @requires_state(GameState.BATTLE)
    @action
    def close_attacks_menu(self) -> None:
        self.logger.info("Closing attacks menu...")
        exit_attacks_btn = self.revomon.screens["battle"].elements[
            "exit_attacks_button"
        ]
        self._click_with_fallback(exit_attacks_btn)

    @requires_state(GameState.BATTLE)
    @action
    def open_battle_bag(self) -> None:
        battle_bag_btn = self.revomon.screens["battle"].elements[
            "team_bag_battle_button"
        ]
        self._click_with_fallback(battle_bag_btn)

    @requires_state(GameState.BATTLE)
    @action
    def close_battle_bag(self) -> None:
        self.logger.info("Closing battle bag...")
        # Assuming ESC closes the bag in battle as well
        exit_btn = self.revomon.screens["main_menu"].elements["exit_button"]
        self._click_with_fallback(exit_btn)

    @requires_state(GameState.BATTLE)
    @action
    def throw_orb(self) -> None:
        """
        Captures a wild Revomon by navigating the bag menu.
        Sequence: Open Bag -> Navigate to Orbs -> Click Orb -> Click Use -> Confirm Yes.
        """
        self.logger.info("Attempting to throw Pokeball...")

        # 1. Open Battle Bag
        battle_bag_btn = self.revomon.screens["battle"].elements[
            "team_bag_battle_button"
        ]
        self._click_with_fallback(battle_bag_btn)

        # 2. Navigate to Orbs Tab
        # Uses smart navigation based on current tab state
        self.go_to_bag_tab("orbs")
        time.sleep(0.5)

        # 3. Click the First Item Slot (The Green Orb)
        slot_1 = self.revomon.screens["battle"].elements["bag_item_slot_1"]
        self._click_with_fallback(slot_1)
        time.sleep(0.8)

        # 4. Click the "Use Item" button
        use_btn = self.revomon.screens["battle"].elements["bag_use_item_button"]
        self._click_with_fallback(use_btn)
        time.sleep(0.8)

        # 5. Click "Yes" on Confirmation Popup
        yes_btn = self.revomon.screens["battle"].elements["bag_confirm_yes_button"]
        self._click_with_fallback(yes_btn)

        # Wait for throw animation
        time.sleep(10.0)

    @requires_state(GameState.BATTLE)
    @action
    def choose_move(self, strategy: Optional[BattleStrategy] = None) -> Optional[str]:
        self.logger.info("Choosing move...")
        try:
            if self.revomon.auto_run is True:
                self.run_from_battle()
                return "ran from battle"

            if self.revomon.auto_battle is True:
                if self.revomon.battle_sub_state != BattleState.ATTACKS_MENU_OPEN:
                    self.open_attacks_menu()

                if strategy is None:
                    self.logger.info("No strategy provided, using RandomMove strategy.")
                    strategy = RandomMove()

                self.logger.info(
                    f"Mon on field moves: {self.revomon.mon_on_field['moves']}"
                )

                valid_moves = []
                for move in self.revomon.mon_on_field["moves"]:
                    name = move.get("name")
                    pp_info = move.get("pp", {})
                    current_pp = pp_info.get("current")

                    # Valid if: Has name AND (PP is unknown OR PP > 0)
                    if name is not None:
                        if current_pp is None or current_pp > 0:
                            valid_moves.append(move)

                if not valid_moves:
                    raise RuntimeError(
                        "No valid moves found (all moves have 0 PP or None names)"
                    )

                self.logger.info(f"Valid moves: {valid_moves}")
                valid_move_names = [move["name"] for move in valid_moves]
                if not valid_move_names:
                    raise RuntimeError("No valid moves available for selection")

                self.logger.info(f"Valid move names: {valid_move_names}")
                move_name = strategy.select_move(valid_move_names)

                self.logger.info(f"Selected move: {move_name}")
                if move_name not in valid_move_names:
                    raise ValueError(
                        f"Strategy selected invalid move '{move_name}'. Valid moves: {valid_move_names}"
                    )

                try:
                    original_index = next(
                        i
                        for i, move in enumerate(self.revomon.mon_on_field["moves"])
                        if move.get("name") == move_name
                    )
                    self.logger.info(f"Move OG index: {original_index}")
                except StopIteration:
                    raise RuntimeError(
                        f"Failed to find move in moves list: {move_name}"
                    )

                move_button_keys = [
                    "player1_mon_move1_button",
                    "player1_mon_move2_button",
                    "player1_mon_move3_button",
                    "player1_mon_move4_button",
                ]

                if 0 <= original_index < len(move_button_keys):
                    move_btn = self.revomon.screens["battle"].elements[
                        move_button_keys[original_index]
                    ]
                    self.logger.info("Clicking move button.")
                    self._click_with_fallback(move_btn)
                    return move_name
                else:
                    raise RuntimeError(
                        f"Move index {original_index} out of range for move: {move_name}"
                    )
            time.sleep(1)
            return None
        except Exception as e:
            self.logger.error(f"Error in choose_move: {str(e)}")
            raise

    @requires_state(GameState.BATTLE)
    @action
    def run_from_battle(self) -> None:
        if self.revomon.battle_sub_state == BattleState.BAG_OPEN:
            self.close_battle_bag()
        elif self.revomon.battle_sub_state == BattleState.ATTACKS_MENU_OPEN:
            self.close_attacks_menu()

        run_btn = self.revomon.screens["battle"].elements["run_button"]
        self._click_with_fallback(run_btn)
        time.sleep(1)
        run_confirm_btn = self.revomon.screens["battle"].elements["run_confirm_button"]
        self._click_with_fallback(run_confirm_btn)

    @requires_state(*LOGGED_IN_STATES)
    @action
    def toggle_auto_run(self) -> None:
        match self.revomon.auto_run:
            case True:
                self.revomon.auto_run = False
            case False:
                self.revomon.auto_run = True

    @requires_state(*LOGGED_IN_STATES)
    @action
    def toggle_auto_battle(self) -> None:
        match self.revomon.auto_battle:
            case True:
                self.revomon.auto_battle = False
            case False:
                self.revomon.auto_battle = True
