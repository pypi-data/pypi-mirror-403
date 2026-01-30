from pathlib import Path

from pymordial import PymordialImage, PymordialPixel


class CurrentTimeText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="current_time_text",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "overworld_assets"
                / "current_time_text.png"
            ),
            position=(1690, 15),
            size=(130, 70),
            confidence=0.6,
        )


class DayTimePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="day_time_pixel",
            og_resolution=(1920, 1080),
            position=(1875, 30),
            pixel_color=(255, 244, 91),
            tolerance=10,
        )


class NightTimePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="night_time_pixel",
            og_resolution=(1920, 1080),
            position=(1875, 30),
            pixel_color=(255, 249, 192),
            tolerance=10,
        )


class MainMenuButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="main_menu_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "overworld_assets"
                / "main_menu_button.png"
            ),
            position=(1785, 185),
            size=(75, 70),
            confidence=0.58,
            image_text="menu",
        )


class MainMenuPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="main_menu_pixel",
            og_resolution=(1920, 1080),
            position=(1827, 218),
            pixel_color=(214, 232, 235),
            tolerance=10,
        )


class ReleaseFirstMonButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="release_first_mon_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "overworld_assets"
                / "release_first_mon_button.png"
            ),
            position=(1785, 350),
            size=(75, 70),
            confidence=0.6,
            image_text="release 1st revomon",
        )


class ReleaseFirstMonPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="release_first_mon_pixel",
            og_resolution=(1920, 1080),
            position=(1827, 401),
            pixel_color=(255, 255, 255),
            tolerance=10,
        )


class AimShootButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="aim_shoot_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "overworld_assets"
                / "aim_shoot_button.png"
            ),
            position=(1785, 515),
            size=(75, 70),
            confidence=0.6,
            image_text="aim for wild revomon",
        )


class AimShootPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="aim_shoot_pixel",
            og_resolution=(1920, 1080),
            position=(1820, 546),
            pixel_color=(254, 254, 254),
            tolerance=10,
        )
