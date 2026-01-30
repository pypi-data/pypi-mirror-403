from pathlib import Path

from pymordial import PymordialImage, PymordialPixel


class StartGameButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="start_game_button",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "start_game_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(740, 592),
            size=(440, 160),
            confidence=0.7,
            image_text="start game",
        )


class StartGamePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="start_game_pixel",
            og_resolution=(1920, 1080),
            position=(956, 635),
            pixel_color=(96, 223, 251),
            tolerance=30,
        )


class QualityDecreaseButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="quality_decrease_button",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "quality_decrease_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(670, 412),
            size=(100, 100),
            confidence=0.7,
        )


class QualityDecreasePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="quality_decrease_pixel",
            og_resolution=(1920, 1080),
            position=(729, 464),
            pixel_color=(187, 238, 255),
            tolerance=30,
        )


class QualityIncreaseButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="quality_increase_button",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "quality_increase_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(740, 592),
            size=(440, 160),
            confidence=0.7,
        )


class QualityIncreasePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="quality_increase_pixel",
            og_resolution=(1920, 1080),
            position=(1198, 464),
            pixel_color=(204, 238, 255),
            tolerance=30,
        )


class CurrentQualityText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="current_quality_text",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "current_quality_text.png"
            ),
            og_resolution=(1920, 1080),
            position=(785, 412),
            size=(350, 100),
            confidence=0.6,
        )


class CurrentVersionText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="current_version_text",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "current_version_text.png"
            ),
            og_resolution=(1920, 1080),
            position=(20, 980),
            size=(150, 70),
            confidence=0.6,
        )


class GameUpdateText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="game_update_text",
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "start_game_assets"
                / "game_update_text.png"
            ),
            og_resolution=(1920, 1080),
            confidence=0.6,
        )


class RevomonBadgePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="revomon_badge_pixel",
            og_resolution=(1920, 1080),
            position=(99, 132),
            pixel_color=(23, 195, 255),
            tolerance=30,
        )
