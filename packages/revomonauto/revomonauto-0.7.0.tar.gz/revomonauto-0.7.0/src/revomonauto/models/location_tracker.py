"""Location tracking via pixel fingerprinting.

Uses 6 horizontal pixels to identify current city/location in the game.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pymordial import PymordialPixel

if TYPE_CHECKING:
    from revomonauto import RevomonController


@dataclass
class LocationSignature:
    """A location identified by 6 pixel colors.

    Attributes:
        city: City name (e.g., 'drassiuscity').
        location: Location within city (e.g., 'insiderevocenter').
        pixels: Tuple of 6 PymordialPixel objects.
        time_cycle: Optional time cycle ('morning', 'afternoon', 'night').
                    If None, signature matches any time.
    """

    city: str
    location: str
    pixels: tuple[PymordialPixel, ...]
    time_cycle: str | None = None


class LocationTracker:
    """Identifies current location using pixel fingerprinting.

    Uses RevomonController.image.check_pixel_color() for matching.
    """

    def __init__(
        self,
        controller: "RevomonController",
        signatures: list[LocationSignature] | None = None,
    ):
        """Initialize the LocationTracker.

        Args:
            controller: RevomonController instance.
            signatures: Optional list of known location signatures.
        """
        self.controller = controller
        self.signatures = signatures if signatures is not None else []
        self.logger = logging.getLogger(__name__)

    def add_signature(self, signature: LocationSignature) -> None:
        """Add a location signature."""
        self.signatures.append(signature)

    def detect_location(
        self,
        screenshot: bytes | None = None,
        time_cycle: str | None = None,
        resolve_revocenter: bool = True,
    ) -> tuple[str, str] | None:
        """Detect current location by matching against known signatures.

        Args:
            screenshot: Optional pre-captured screenshot. If None, captures new one.
            time_cycle: Optional time cycle to filter signatures.
                        If None, tries to auto-detect using controller.
            resolve_revocenter: If True and in a generic revocenter, walks out
                                to detect city and walks back in.

        Returns:
            Tuple of (city, location) if match found, None otherwise.
        """
        if not self.signatures:
            self.logger.warning("No signatures registered.")
            return None

        # Capture screenshot if not provided
        if screenshot is None:
            try:
                screenshot = self.controller.capture_screen()
            except Exception as e:
                self.logger.error(f"Failed to capture screenshot: {e}")
                return None

        # Auto-detect time cycle if not provided
        if time_cycle is None:
            try:
                time_cycle = self.controller.get_current_time_cycle(screenshot)
                self.logger.debug(f"Auto-detected time cycle: {time_cycle}")
            except Exception as e:
                self.logger.debug(f"Could not detect time cycle: {e}")
                time_cycle = None

        # Filter signatures by time cycle
        candidates = [
            sig
            for sig in self.signatures
            if sig.time_cycle is None or sig.time_cycle == time_cycle
        ]

        # Try to match signatures
        for sig in candidates:
            if self._match_signature(screenshot, sig):
                self.logger.info(f"Location detected: {sig.city}-{sig.location}")
                result = (sig.city, sig.location)

                # Check if we need to resolve a generic revocenter
                if resolve_revocenter and self.is_generic_revocenter(
                    sig.city, sig.location
                ):
                    self.logger.info(
                        f"Generic revocenter detected ({sig.city}) - resolving city..."
                    )
                    return self._resolve_revocenter_location()

                return result

        self.logger.debug("No matching signature found.")

        # If no match and resolve enabled, check if we're in a revocenter via screen detection
        if resolve_revocenter:
            self.logger.info("No signature match, checking if in revocenter...")
            try:
                if self.controller.revomon.screens["revocenter"].is_current_screen(
                    self.controller
                ):
                    self.logger.info(
                        "In revocenter but no signature match - resolving..."
                    )
                    return self._resolve_revocenter_location()
            except Exception as e:
                self.logger.debug(f"Revocenter screen check failed: {e}")

        return None

    def _match_signature(
        self,
        screenshot: bytes,
        signature: LocationSignature,
    ) -> bool:
        """Check if all 6 pixels match using check_pixel_color.

        Args:
            screenshot: Screenshot bytes.
            signature: LocationSignature to match against.

        Returns:
            True if all pixels match, False otherwise.
        """
        for pixel in signature.pixels:
            try:
                match = self.controller.ui.check_pixel_color(
                    pymordial_pixel=pixel,
                    pymordial_screenshot=screenshot,
                )
                if not match:
                    return False
            except Exception as e:
                self.logger.debug(f"Pixel check failed: {e}")
                return False

        return True

    def is_generic_revocenter(
        self,
        city: str | None,
        location: str | None,
    ) -> bool:
        """Check if location is a generic (non-Drassius) revocenter.

        Args:
            city: Detected city name.
            location: Detected location name.

        Returns:
            True if in a generic revocenter that needs resolution.
        """
        if location != "insiderevocenter":
            return False
        # Drassius revocenter is unique and can be identified
        if city == "drassiuscity":
            return False
        # Generic/unknown city + inside revocenter = needs resolution
        return city is None or city in ("unknown", "generic")

    def _resolve_revocenter_location(self) -> tuple[str, str] | None:
        """Resolve city when inside a generic revocenter.

        Walks out of revocenter to detect city, then walks back in.
        Uses shared scripts from routes.yaml (exit_revocenter, enter_revocenter).

        Returns:
            Tuple of (city, "insiderevocenter") if resolved, None on failure.
        """
        import time

        self.logger.info("Resolving revocenter location - walking outside...")

        # Get shared scripts from Navigator's registry
        try:
            navigator = self.controller.navigator
            if navigator is None:
                self.logger.error("Navigator not initialized")
                return None

            exit_script = navigator.registry.get_script("exit_revocenter")
            enter_script = navigator.registry.get_script("enter_revocenter")

            if not exit_script:
                self.logger.error("exit_revocenter script not found in routes.yaml")
                return None
        except Exception as e:
            self.logger.error(f"Failed to get revocenter scripts: {e}")
            return None

        # Execute exit script
        try:
            self.logger.info("Executing exit_revocenter script...")
            self.controller.execute_movement_script(exit_script)
            time.sleep(3.0)  # Brief pause after movement
        except Exception as e:
            self.logger.error(f"Failed to exit revocenter: {e}")
            return None

        # Detect location outside (without recursive resolution)
        result = self.detect_location(resolve_revocenter=False)
        if result is None:
            self.logger.warning("Could not detect location outside revocenter")
            # Still try to walk back in
            if enter_script:
                try:
                    self.controller.execute_movement_script(enter_script)
                except Exception:
                    pass
            return None

        detected_city, detected_location = result
        self.logger.info(f"Detected outside: {detected_city}-{detected_location}")

        # Execute enter script to go back in
        if enter_script:
            self.logger.info("Executing enter_revocenter script...")
            try:
                self.controller.execute_movement_script(enter_script)
                time.sleep(3.0)
            except Exception as e:
                self.logger.error(f"Failed to re-enter revocenter: {e}")
                # Still return the city we detected

        return (detected_city, "insiderevocenter")
