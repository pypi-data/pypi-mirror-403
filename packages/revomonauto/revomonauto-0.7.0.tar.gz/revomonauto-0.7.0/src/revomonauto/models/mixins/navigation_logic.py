"""
Navigation logic mixin for RevomonApp.

Handles all movement and world interaction logic.
"""

import math
import time
from io import BytesIO

import numpy as np
from PIL import Image

from ..action import action
from ..states import GameState, requires_state

# Joystick Config
JOYSTICK_CENTER_X = 300
JOYSTICK_CENTER_Y = 900
JOYSTICK_RADIUS = 100

# Game Config
MAX_HUNT_ATTEMPTS = 12
HUNT_SWIPE_COMMAND = [1200, 540, 1000, 540, 200]
DEFAULT_CITY = "drassiuscity"
DEFAULT_LOCATION = "insiderevocenter"


class NavigationLogicMixin:
    """Mixin providing all navigation-related logic for RevomonApp.

    Assumes the following attributes exist on the parent class:
    - self.pymordial_controller
    - self.screens
    - self.logger
    - self.game_state
    - self.navigator
    - self._click_with_fallback()
    - self.update_world_state()
    """

    def _calculate_swipe_command(
        self, angle: float, speed: float, duration: float
    ) -> str:
        speed = max(0.0, min(10.0, speed))
        duration = max(0.1, duration)

        distance = speed * JOYSTICK_RADIUS
        angle_rad = math.radians(angle)
        offset_x = distance * math.sin(angle_rad)
        offset_y = -distance * math.cos(angle_rad)

        end_x = int(JOYSTICK_CENTER_X + offset_x)
        end_y = int(JOYSTICK_CENTER_Y + offset_y)
        duration_ms = int(duration * 1000)

        return f"input swipe {JOYSTICK_CENTER_X} {JOYSTICK_CENTER_Y} {end_x} {end_y} {duration_ms}"

    # --- START MOVEMENT LOGIC ---
    @requires_state(GameState.OVERWORLD, GameState.BATTLE)
    @action
    def move(self, angle: float, speed: float = 100.0, duration: float = 1.0) -> None:
        command = self._calculate_swipe_command(angle, speed, duration)
        self.logger.debug(f"Moving: angle={angle}, cmd={command}")
        self.run_command(command)

    @requires_state(GameState.OVERWORLD, GameState.BATTLE)
    @action
    def perform_idle_sequence(self) -> None:
        """Executes the standard idle movement pattern in a single ADB request."""
        # 1. Move Back
        cmd1 = self._calculate_swipe_command(180, 0.5, 0.5)
        # 2. Move Forward
        cmd2 = self._calculate_swipe_command(0, 0.5, 0.5)
        # 3. Move Back
        # cmd3 = self._calculate_swipe_command(180, 0.5, 0.5)

        # Chain commands with '&&' so they execute sequentially on the device
        full_command = f"{cmd1} && sleep 0.5 && {cmd2} && sleep 0.5"

        self.logger.debug("Executing idle sequence bundle.")
        self.run_command(full_command)

    @requires_state(GameState.OVERWORLD, GameState.BATTLE)
    @action
    def execute_movement_script(
        self, script: list[tuple[float, float, float]], detect_portal: bool = False
    ) -> bool:
        """Execute a list of movement commands as a single batch.

        Args:
            script: List of tuples [(angle, speed, duration), ...]
            detect_portal: If True, monitor for portal transition during movement.

        Returns:
            True if portal detected during movement (only when detect_portal=True),
            False otherwise.
        """
        if not script:
            self.logger.warning("Empty movement script provided.")
            return False

        cmds = []
        for step in script:
            angle, speed, duration = step
            cmd = self._calculate_swipe_command(angle, speed, duration)
            cmds.append(cmd)

        # Chain commands with '&&' for sequential execution on Android
        full_command = " && ".join(cmds)
        total_duration = sum(step[2] for step in script)

        portal_detected = False

        if detect_portal:
            import threading

            stop_monitoring = threading.Event()

            def monitor_for_portal():
                """Background thread to check for black screen during movement."""
                nonlocal portal_detected
                adb = self.adb
                check_interval = 0.05  # Check every 50ms
                consecutive_dark_frames = 0
                required_consecutive = 3  # Need 3 dark frames to confirm portal
                check_count = 0

                while not stop_monitoring.is_set():
                    try:
                        screenshot_bytes = adb.capture_screenshot()
                        pil_img = Image.open(BytesIO(screenshot_bytes))
                        gray = pil_img.convert("L")
                        mean_brightness = np.mean(np.array(gray))
                        check_count += 1

                        # Debug log every check
                        self.logger.debug(
                            f"Portal check #{check_count}: brightness={mean_brightness:.1f}, consecutive_dark={consecutive_dark_frames}"
                        )

                        if mean_brightness < 10:
                            consecutive_dark_frames += 1
                            self.logger.info(
                                f"Dark frame #{consecutive_dark_frames} detected (brightness: {mean_brightness:.1f})"
                            )
                            if consecutive_dark_frames >= required_consecutive:
                                self.logger.info(
                                    f"PORTAL CONFIRMED! ({consecutive_dark_frames} consecutive dark frames)"
                                )
                                portal_detected = True
                                return
                        else:
                            if consecutive_dark_frames > 0:
                                self.logger.debug(
                                    f"Dark streak broken at {consecutive_dark_frames}"
                                )
                            consecutive_dark_frames = 0  # Reset if not dark
                    except Exception as e:
                        self.logger.debug(f"Portal monitor error: {e}")
                    time.sleep(check_interval)

            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_for_portal, daemon=True)
            monitor_thread.start()

            # Execute movement
            self.logger.info(
                f"Executing movement script with {len(cmds)} steps (portal detection ON)."
            )
            self.run_command(full_command)
            time.sleep(total_duration)

            # Stop monitoring and wait for thread
            stop_monitoring.set()
            monitor_thread.join(timeout=0.5)
        else:
            # Normal execution without portal detection
            self.logger.info(f"Executing movement script with {len(cmds)} steps.")
            self.run_command(full_command)
            time.sleep(total_duration)

        return portal_detected

    def wait_for_portal_transition(self, timeout: float = 5.0) -> bool:
        """Wait for portal transition (black screen) to be detected.

        Portal transitions show a completely black loading screen.
        Uses mean brightness check (< 40 on 0-255 scale = portal detected).

        Args:
            timeout: Maximum time to wait for transition in seconds.

        Returns:
            True if portal transition detected, False if timeout.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                screenshot_bytes = self.capture_screenshot()
                pil_img = Image.open(BytesIO(screenshot_bytes))

                # Convert to grayscale and check brightness
                gray = pil_img.convert("L")
                mean_brightness = np.mean(np.array(gray))

                if mean_brightness < 10:
                    self.logger.info(
                        f"Portal transition detected! (brightness: {mean_brightness:.1f})"
                    )
                    return True
            except Exception as e:
                self.logger.debug(f"Portal detection screenshot error: {e}")

            time.sleep(0.1)

        self.logger.info("Portal transition NOT detected within timeout.")
        return False

    # --- END MOVEMENT LOGIC ---

    # --- NPC & HEALING LOGIC ---
    @requires_state(GameState.OVERWORLD)
    @action
    def talk_to_npc(self, npc_element, dialog_skips: int = 0) -> None:
        """
        Interacts with an NPC.
        Assumes standing in front of them or clicking their UI element.
        """
        self.logger.info(f"Attempting to talk to {npc_element.label}...")
        self._click_with_fallback(npc_element)

        # If we expect dialog, skip it
        if dialog_skips > 0:
            time.sleep(1.0)  # Wait for dialog to open
            center_screen_coord = (960, 540)
            for _ in range(dialog_skips):
                self.click_coord(center_screen_coord)
                time.sleep(1.5)
        else:
            # For instant interaction (healing), just wait a bit for effect
            time.sleep(2.0)

        self.logger.info("Finished NPC interaction.")

    @requires_state(GameState.OVERWORLD)
    @action
    def heal_party(self):
        self.logger.info("❤️❤️❤️ HEALING PROTOCOL INITIATED ❤️❤️❤️")

        # Navigator is auto-initialized when we first enter overworld
        # No need to lazy load it here anymore

        # 1. Reset to last waypoint (portal) before navigation
        # This ensures we're at a known location in the route graph
        self.logger.info("Resetting to last waypoint before navigation...")
        self.reset_position()

        # Update our current position to the last waypoint
        # Note: We should track the last portal entered separately in the future
        # For now, we rely on the default location
        if not self.revomon.current_city or not self.revomon.current_location:
            self.logger.warning(
                f"Current location unknown after reset. Defaulting to '{DEFAULT_CITY}' - '{DEFAULT_LOCATION}'."
            )
            self.revomon.current_city = DEFAULT_CITY
            self.revomon.current_location = DEFAULT_LOCATION

        # Capture start position for return trip
        start_city = self.revomon.current_city
        start_loc = self.revomon.current_location

        # 2. Navigate to Center
        self.logger.info("Navigating to closest Revocenter...")
        success = self.navigator.navigate_to_closest(
            start_city, start_loc, "insiderevocenter"
        )

        if not success:
            self.logger.error("Failed to navigate to Revocenter. Aborting heal.")
            return

        # 3. Talk to Nurse
        nurse_interaction_point = self.revomon.screens["revocenter"].elements[
            "drassius_nurse_npc_pixel"
        ]
        self.talk_to_npc(nurse_interaction_point, dialog_skips=0)

        # 4. Reset Internal State
        # self.revomon.mon_on_field access might need checking type
        self.revomon.mon_on_field["current_hp_percentage"] = 100.0
        for move in self.revomon.mon_on_field["moves"]:
            if move.get("pp"):
                move["pp"]["current"] = move["pp"]["total"]
        self.logger.info("Party healed. Stats reset.")

        # 5. Return to start location (the waypoint we reset to)
        self.logger.info(f"Returning to {start_city} - {start_loc}...")
        self.navigator.navigate_to(
            self.revomon.current_city,
            self.revomon.current_location,
            start_city,
            start_loc,
        )

    # --- END NPC & HEALING LOGIC ---
