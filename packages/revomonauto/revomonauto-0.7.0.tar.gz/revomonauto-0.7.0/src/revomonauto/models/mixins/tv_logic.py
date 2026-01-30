"""
TV logic mixin for RevomonApp.

Handles all TV screen interactions and revomon scanning.
"""

import json
import random
import threading
import time
from pathlib import Path

import requests

from ..action import action
from ..states import GameState, requires_state
from ..strategies import RevomonTextStrategy

REVOMON_API_URL = "https://api.revomon.io/revomon"
REVOMON_DB_PATH = Path(__file__).parent.parent.parent / "revomon_db.json"
REVOMON_DB_LOCK = threading.Lock()


class TVLogicMixin:
    """Mixin providing all TV-related logic for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.game_state
    - self._click_with_fallback()
    """

    # --- BEGIN TV LOGIC ---
    # --- BEGIN TV LOGIC ---
    @requires_state(GameState.OVERWORLD)
    @action
    def open_tv(self) -> None:
        tv_screen_button = self.revomon.screens["revocenter"].elements[
            "tv_screen_pixel"
        ]
        self._click_with_fallback(tv_screen_button, times=2)
        # Initialize executor if needed
        if not hasattr(self, "_tv_executor"):
            import concurrent.futures

            # Use a limited number of workers to prevent system overload
            self._tv_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

    @requires_state(GameState.TV)
    @action
    def close_tv(self) -> None:
        tv_exit_button = self.revomon.screens["tv"].elements["tv_exit_button"]
        self._click_with_fallback(tv_exit_button)

    @requires_state(GameState.TV)
    @action
    def tv_search_for_revomon(self, revomon_name: str) -> None:
        tv_search_input = self.revomon.screens["tv"].elements["tv_search_input"]
        self._click_with_fallback(tv_search_input)
        time.sleep(1)
        self.type_text(revomon_name, enter=True)
        time.sleep(1)
        tv_search_button = self.revomon.screens["tv"].elements["tv_search_button"]
        self._click_with_fallback(tv_search_button)
        self.revomon.mon_searching_for = revomon_name

    @requires_state(GameState.TV)
    @action
    def select_tv_slot(self, slot_number: int) -> None:
        if slot_number == self.revomon.tv_slot_selected:
            self.logger.info(f"SLOT {slot_number} ALREADY SELECTED")
            return
        if slot_number < 1 or slot_number > 30:
            self.logger.warning(
                f"SLOT {slot_number} IS OUT OF RANGE. MIN IS 1, MAX IS 30."
            )
            return
        self.logger.info(f"SELECTING SLOT #: {slot_number}")
        tv_slot_button = self.revomon.screens["tv"].elements[
            f"tv_slot{slot_number}_button"
        ]
        self.click_coord(tv_slot_button.center)
        self.revomon.tv_slot_selected = slot_number
        self.revomon.is_mon_selected = True

        # Wait for UI to update then capture screen synchronously
        time.sleep(random.uniform(1.5, 3.5))
        screenshot_bytes = self.capture_screen()

        if screenshot_bytes is not None:
            # Offload processing to background thread
            if not hasattr(self, "_tv_executor"):
                import concurrent.futures

                self._tv_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

            self._tv_executor.submit(
                self._extract_revomon_tv_info_background, screenshot_bytes
            )
        else:
            self.logger.error("Failed to capture screenshot for slot processing")

    # TODO: Add a way to detremine the total number of pages
    @requires_state(GameState.TV)
    @action
    def tv_next_page(self) -> None:
        if self.revomon.tv_current_page == 18:
            self.logger.warning("Already on the last page")
            return
        tv_next_page_button = self.revomon.screens["tv"].elements["tv_next_page_button"]
        self._click_with_fallback(tv_next_page_button)
        self.revomon.tv_slot_selected = 0
        self.revomon.is_mon_selected = False
        self.revomon.tv_current_page += 1
        time.sleep(1)

    @requires_state(GameState.TV)
    @action
    def tv_previous_page(self) -> None:
        if self.revomon.tv_current_page == 1:
            self.logger.warning("Already on the first page")
            return
        tv_previous_page_button = self.revomon.screens["tv"].elements[
            "tv_previous_page_button"
        ]
        self._click_with_fallback(tv_previous_page_button)
        self.revomon.tv_slot_selected = 0
        self.revomon.is_mon_selected = False
        self.revomon.tv_current_page -= 1
        time.sleep(1)

    def _extract_revomon_tv_info_background(self, screenshot_bytes: bytes) -> None:
        """Extract revomon info from TV screen via OCR and fetch from API (Background Task)."""
        try:
            self.logger.info("Extracting revomon tv info (background)...")

            # Extract mon catch ID via OCR
            mon_catch_id_element = self.revomon.screens["tv"].elements["tv_mon_id_text"]
            mon_move1_element = self.revomon.screens["tv"].elements["tv_mon_move1_text"]
            mon_move2_element = self.revomon.screens["tv"].elements["tv_mon_move2_text"]
            mon_move3_element = self.revomon.screens["tv"].elements["tv_mon_move3_text"]
            mon_move4_element = self.revomon.screens["tv"].elements["tv_mon_move4_text"]
            cropped_imgs = self.extract_regions(
                pymordial_elements=[
                    mon_catch_id_element,
                    mon_move1_element,
                    mon_move2_element,
                    mon_move3_element,
                    mon_move4_element,
                ],
                image=screenshot_bytes,
            )

            mon_catch_id_ocr_result = self.read_text(
                cropped_imgs[0], strategy=RevomonTextStrategy()
            )
            if not mon_catch_id_ocr_result:
                self.logger.warning("OCR failed to extract mon catch ID")
                return
            mon_catch_id = mon_catch_id_ocr_result[0].replace("id ", "").strip()
            self.logger.info(f"Mon catch ID: {mon_catch_id}")
            while True:
                mon_move1_ocr_result = self.read_text(
                    cropped_imgs[1], strategy=RevomonTextStrategy()
                )
                if not mon_move1_ocr_result:
                    self.logger.warning("OCR failed to extract mon move 1")
                    mon_move1 = None
                    mon_move2 = None
                    mon_move3 = None
                    mon_move4 = None
                    break
                else:
                    mon_move1 = "".join(
                        c for c in mon_move1_ocr_result[0] if c.isalpha() or c == " "
                    ).strip()
                self.logger.info(f"Mon move 1: {mon_move1}")

                mon_move2_ocr_result = self.read_text(
                    cropped_imgs[2], strategy=RevomonTextStrategy()
                )
                if not mon_move2_ocr_result:
                    self.logger.warning("OCR failed to extract mon move 2")
                    mon_move2 = None
                    mon_move3 = None
                    mon_move4 = None
                    break
                else:
                    mon_move2 = "".join(
                        c for c in mon_move2_ocr_result[0] if c.isalpha() or c == " "
                    ).strip()
                self.logger.info(f"Mon move 2: {mon_move2}")

                mon_move3_ocr_result = self.read_text(
                    cropped_imgs[3], strategy=RevomonTextStrategy()
                )
                if not mon_move3_ocr_result:
                    self.logger.warning("OCR failed to extract mon move 3")
                    mon_move3 = None
                    mon_move4 = None
                    break
                else:
                    mon_move3 = "".join(
                        c for c in mon_move3_ocr_result[0] if c.isalpha() or c == " "
                    ).strip()
                self.logger.info(f"Mon move 3: {mon_move3}")

                mon_move4_ocr_result = self.read_text(
                    cropped_imgs[4], strategy=RevomonTextStrategy()
                )
                if not mon_move4_ocr_result:
                    self.logger.warning("OCR failed to extract mon move 4")
                    mon_move4 = None
                    break
                else:
                    mon_move4 = "".join(
                        c for c in mon_move4_ocr_result[0] if c.isalpha() or c == " "
                    ).strip()
                self.logger.info(f"Mon move 4: {mon_move4}")
                break

            # Fetch revomon data from API
            revomon_data = self._fetch_revomon_data(mon_catch_id)
            if revomon_data:
                self.logger.info("=== Revomon Data ===")
                self.logger.info(
                    f"  ID (Catched): {revomon_data.get('idCatchedRevomon')}"
                )
                self.logger.info(f"  ID (Species): {revomon_data.get('idRevomon')}")
                self.logger.info(f"  Name: {revomon_data.get('name')}")
                self.logger.info(f"  Rarity: {revomon_data.get('rarity')}")
                self.logger.info(f"  Description: {revomon_data.get('description')}")
                self.logger.info(
                    f"  Type: {revomon_data.get('type1')}/{revomon_data.get('type2')}"
                )
                self.logger.info(f"  Gender: {revomon_data.get('gender')}")
                self.logger.info(f"  Nature: {revomon_data.get('nature')}")
                self.logger.info(f"  Ability: {revomon_data.get('ability')}")
                self.logger.info(f"  Shiny: {revomon_data.get('shiny')}")
                self.logger.info(f"  Is NFT: {revomon_data.get('isNft')}")
                self.logger.info(
                    f"  IVs - HP:{revomon_data.get('ivhp')} ATK:{revomon_data.get('ivatk')} DEF:{revomon_data.get('ivdef')} SPA:{revomon_data.get('ivspa')} SPD:{revomon_data.get('ivspd')} SPE:{revomon_data.get('ivspe')}"
                )
                self.logger.info(f"  Move 1: {mon_move1}")
                self.logger.info(f"  Move 2: {mon_move2}")
                self.logger.info(f"  Move 3: {mon_move3}")
                self.logger.info(f"  Move 4: {mon_move4}")
                # Store for later use
                revomon_data.update(
                    {
                        "moves": [
                            mon_move1,
                            mon_move2,
                            mon_move3,
                            mon_move4,
                        ],
                    }
                )
                self._save_revomon_to_db(revomon_data)

            self.logger.info("Revomon tv info extracted successfully")
        except Exception as e:
            self.logger.error(f"Error extracting revomon tv info: {e}")

    def _fetch_revomon_data(self, catch_id: str) -> dict | None:
        """Fetch revomon data from the Revomon API.

        Args:
            catch_id: The catched revomon ID.

        Returns:
            Dict with revomon data or None if not found/error.
        """
        try:
            url = f"{REVOMON_API_URL}/{catch_id}"
            self.logger.debug(f"Fetching revomon data from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("error"):
                self.logger.warning(f"API error: {data['error']}")
                return None

            return data.get("data", {}).get("catchedRevomon")
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch revomon data: {e}")
            return None

    def _save_revomon_to_db(self, revomon_data: dict) -> None:
        """Save revomon data to JSON database file.

        Stores by catch ID, updates if already exists.

        Args:
            revomon_data: The revomon data dict to save.
        """
        try:
            # Ensure data directory exists
            REVOMON_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Use lock to prevent concurrent write issues
            with REVOMON_DB_LOCK:
                # Load existing DB or create empty dict
                if REVOMON_DB_PATH.exists():
                    with open(REVOMON_DB_PATH, "r", encoding="utf-8") as f:
                        db = json.load(f)
                else:
                    db = {}

                # Use catch ID as key
                catch_id = str(revomon_data.get("idCatchedRevomon"))
                db[catch_id] = revomon_data

                # Save back to file
                with open(REVOMON_DB_PATH, "w", encoding="utf-8") as f:
                    json.dump(db, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved revomon {catch_id} to database")
        except Exception as e:
            self.logger.error(f"Failed to save revomon to database: {e}")

    # --- END TV SCREEN LOGIC ---
