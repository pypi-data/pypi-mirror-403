import os
import random
import re
from abc import ABC, abstractmethod

import cv2
import numpy as np
from pymordial.core.blueprints.extract_strategy import PymordialExtractStrategy
from pymordialblue.utils.configs import get_config
from pymordialblue.utils.extract_strategies import DefaultExtractStrategy

_CONFIG = get_config()


# --- Revomon Strategy Constants ---
DEFAULT_DENOISE_STRENGTH = _CONFIG["extract_strategy"]["default"]["denoise_strength"]
DEFAULT_DENOISE_TEMPLATE_WINDOW = _CONFIG["extract_strategy"]["default"][
    "denoise_template_window"
]
DEFAULT_DENOISE_SEARCH_WINDOW = _CONFIG["extract_strategy"]["default"][
    "denoise_search_window"
]
THRESHOLD_BINARY_MAX = _CONFIG["extract_strategy"]["default"]["threshold_binary_max"]
INVERSION_THRESHOLD_MEAN = _CONFIG["extract_strategy"]["default"][
    "inversion_threshold_mean"
]
MODE_DEFAULT = "default"
MODE_MOVE = "move"
MODE_LEVEL = "level"

MOVE_UPSCALE_FACTOR = _CONFIG["extract_strategy"]["revomon"]["move"]["upscale_factor"]
MOVE_BUTTON_CROP_LEFT_RATIO = _CONFIG["extract_strategy"]["revomon"]["move"][
    "crop_left_ratio"
]
MOVE_BUTTON_CROP_BOTTOM_RATIO = _CONFIG["extract_strategy"]["revomon"]["move"][
    "crop_bottom_ratio"
]
MOVE_BUTTON_PADDING = _CONFIG["extract_strategy"]["revomon"]["move"]["padding"]
PADDING_VALUE_WHITE = _CONFIG["extract_strategy"]["revomon"]["padding_value_white"]

LEVEL_TEXT_CROP_LEFT_RATIO = _CONFIG["extract_strategy"]["revomon"]["level"][
    "crop_left_ratio"
]


TESSERACT_BASE_CONFIG = _CONFIG["extract_strategy"]["tesseract"]["base_config"]
PSM_SINGLE_LINE = _CONFIG["extract_strategy"]["tesseract"]["psm"]["single_line"]
PSM_BLOCK = _CONFIG["extract_strategy"]["tesseract"]["psm"]["block"]

MOVE_BUTTON_WHITELIST_CONFIG = _CONFIG["extract_strategy"]["revomon"]["move"][
    "whitelist_config"
]
LEVEL_WHITELIST_CONFIG = _CONFIG["extract_strategy"]["revomon"]["level"][
    "whitelist_config"
]


class BattleStrategy(ABC):
    """
    Abstract base class for battle strategies.
    """

    @abstractmethod
    def select_move(self, valid_move_names: list[str]) -> str:
        """
        Selects a move from the list of valid move names.

        Args:
            valid_move_names (list[str]): A list of valid move names.

        Returns:
            str: The name of the selected move.
        """
        pass


class RandomMove(BattleStrategy):
    """
    A battle strategy that selects a random move.
    """

    def select_move(self, valid_move_names: list[str]) -> str:
        """Selects a random move from the list of valid move names.

        Args:
            valid_move_names (list[str]): A list of valid move names.

        Returns:
            str: The name of the selected move.
        """
        if not valid_move_names:
            raise RuntimeError("No valid moves available for random selection")
        return random.choice(valid_move_names)


class RevomonTextStrategy(PymordialExtractStrategy):
    """Strategy for Revomon UI images.

    Attributes:
        mode: The processing mode ("default", "move", "level").
        debug_output_dir: Directory to save debug images.
    """

    def __init__(self, mode: str = MODE_DEFAULT, debug_output_dir: str | None = None):
        """Initializes theRevomonTextStrategy.

        Args:
            mode: The processing mode.
                "default": generic processing.
                "move": crops icon/energy bar, upscales 3x.
                "level": crops "lvl" text, returns digits only.
            debug_output_dir: If provided, saves preprocessed images to this
                directory for debugging.
        """
        self.mode = mode
        self.debug_output_dir = debug_output_dir
        self._default = DefaultExtractStrategy()
        self._debug_counter = 0

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocesses the image based on the selected mode."""
        if self.mode == MODE_MOVE:
            # Custom pipeline for move buttons
            h, w = image.shape[:2]
            y_end = h - int(h * MOVE_BUTTON_CROP_BOTTOM_RATIO)
            cropped = image[0:y_end, int(w * MOVE_BUTTON_CROP_LEFT_RATIO) :]

            # Upscale 3x for move buttons (helps with small text like 'Phantom Force')
            processed = cv2.resize(
                cropped,
                None,
                fx=MOVE_UPSCALE_FACTOR,
                fy=MOVE_UPSCALE_FACTOR,
                interpolation=cv2.INTER_CUBIC,
            )
            # Grayscale
            gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            # Denoise (keep it low to avoid blurring)
            denoised = cv2.fastNlMeansDenoising(
                gray,
                None,
                DEFAULT_DENOISE_STRENGTH,
                DEFAULT_DENOISE_TEMPLATE_WINDOW,
                DEFAULT_DENOISE_SEARCH_WINDOW,
            )
            # Otsu threshold
            _, thresh = cv2.threshold(
                denoised, 0, THRESHOLD_BINARY_MAX, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            # Invert if background is dark (it usually is for buttons)
            if np.mean(thresh) < INVERSION_THRESHOLD_MEAN:
                thresh = cv2.bitwise_not(thresh)

            processed = thresh

            # Add padding
            processed = cv2.copyMakeBorder(
                processed,
                MOVE_BUTTON_PADDING,
                MOVE_BUTTON_PADDING,
                MOVE_BUTTON_PADDING,
                MOVE_BUTTON_PADDING,
                cv2.BORDER_CONSTANT,
                value=PADDING_VALUE_WHITE,
            )
        elif self.mode == MODE_LEVEL:
            # Custom pipeline for level indicators: crop out "lvl" text
            _, w = image.shape[:2]
            cropped = image[:, int(w * LEVEL_TEXT_CROP_LEFT_RATIO) :]
            processed = self._default.preprocess(cropped)
        else:
            # Use default pipeline for other modes
            processed = self._default.preprocess(image)

        # Save debug image if debug directory is set
        if self.debug_output_dir:
            os.makedirs(self.debug_output_dir, exist_ok=True)
            debug_path = os.path.join(
                self.debug_output_dir,
                f"debug_{self.mode}_{self._debug_counter:03d}.png",
            )
            cv2.imwrite(debug_path, processed)
            self._debug_counter += 1

        return processed

    def postprocess_text(self, text: str) -> str:
        """Clean up OCR artifacts for Revomon UI text."""
        if self.mode == MODE_MOVE:
            # Replace newlines with spaces (multi-line moves like "Phantom Force")
            text = text.replace("\n", " ").replace("\r", " ")
            # Remove multiple spaces
            text = re.sub(r"\s+", " ", text)
            # Strip leading/trailing punctuation artifacts (commas, periods, semicolons, etc.)
            text = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", text)
            # Remove any words less than 2 characters
            text = re.sub(r"\b\w{1,2}\b", "", text)
            # Final trim
            text = text.strip()
        elif self.mode == MODE_LEVEL:
            # For levels, just strip whitespace (we only get digits anyway)
            text = text.strip()

        return text

    def tesseract_config(self) -> str:
        """Returns the Tesseract configuration for the current mode."""
        base = TESSERACT_BASE_CONFIG
        if self.mode == MODE_MOVE:
            # Use PSM 6 (Block) for move buttons to handle multi-word text
            return f"{base} --psm {PSM_BLOCK} {MOVE_BUTTON_WHITELIST_CONFIG}"
        elif self.mode == MODE_LEVEL:
            # Use PSM 7 (Single Line) with digit-only whitelist
            return f"{base} --psm {PSM_SINGLE_LINE} {LEVEL_WHITELIST_CONFIG}"
        else:
            return f"{base} --psm {PSM_BLOCK}"
