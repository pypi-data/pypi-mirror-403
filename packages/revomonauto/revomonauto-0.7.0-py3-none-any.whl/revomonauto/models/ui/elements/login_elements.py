from pathlib import Path

from pymordial import PymordialImage, PymordialPixel


class LoginButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="login_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "login_assets"
                / "login_button.png"
            ),
            position=(748, 436),
            size=(425, 160),
            confidence=0.8,
            image_text="login",
        )


class ReloginButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="relogin_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "login_assets"
                / "relogin_button.png"
            ),
            position=(748, 436),
            size=(425, 160),
            confidence=0.8,
            image_text="relogin",
        )


class LoginPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="login_pixel",
            og_resolution=(1920, 1080),
            position=(955, 569),
            pixel_color=(71, 113, 178),
            tolerance=10,
        )


class DisconnectButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="disconnect_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "login_assets"
                / "disconnect_button.png"
            ),
            position=(1550, 830),
            size=(300, 85),
            confidence=0.7,
            image_text="disconnect",
        )


class DisconnectPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="disconnect_pixel",
            position=(1693, 855),
            pixel_color=(224, 190, 105),
            og_resolution=(1920, 1080),
            tolerance=10,
        )


class ServerSelectPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="server_select_pixel",
            position=(1649, 1023),
            pixel_color=(71, 114, 176),
            og_resolution=(1920, 1080),
            tolerance=10,
        )


class RevomonBadgePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="revomon_badge_pixel",
            position=(964, 97),
            pixel_color=(20, 198, 255),
            og_resolution=(1920, 1080),
            tolerance=10,
        )
