from pathlib import Path

from pymordial import PymordialImage, PymordialPixel

BASE_DIR = Path(__file__).parent.parent


class ChatButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="chat_button",
            og_resolution=(1920, 1080),
            filepath=str(BASE_DIR / "assets" / "shared_assets" / "chat_button.png"),
            position=(1820, 1000),
            size=(90, 70),
            confidence=0.6,
        )


class BattleChatButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="battle_chat_button",
            og_resolution=(1920, 1080),
            filepath=str(
                BASE_DIR / "assets" / "shared_assets" / "battle_chat_button.png"
            ),
            position=(1530, 140),
            size=(140, 70),
            confidence=0.6,
            image_text="battle",
        )


class GeneralChatButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="general_chat_button",
            og_resolution=(1920, 1080),
            filepath=str(
                BASE_DIR / "assets" / "shared_assets" / "general_chat_button.png"
            ),
            position=(1725, 140),
            size=(140, 70),
            confidence=0.6,
            image_text="general",
        )


class ChatLogImage(PymordialImage):
    def __init__(self):
        super().__init__(
            label="chat_log_image",
            og_resolution=(1920, 1080),
            filepath=str(BASE_DIR / "assets" / "shared_assets" / "chat_log_image.png"),
            position=(1490, 220),
            size=(435, 775),
            confidence=0.6,
        )


class ExitMenuButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="exit_menu_button",
            og_resolution=(1920, 1080),
            position=(1800, 5),
            size=(110, 110),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "shared_assets"
                / "exit_menu_button.png"
            ),
            confidence=0.7,
        )


class ExitMenuPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="exit_menu_pixel",
            og_resolution=(1920, 1080),
            position=(1857, 62),
            pixel_color=(155, 204, 233),
            tolerance=10,
        )


# =============================================================================
# Submenu Title Text Elements (for OCR-based screen detection)
# =============================================================================


class SubmenuTitleText(PymordialImage):
    """Standard submenu title region for OCR detection.

    Used by: Wardrobe, Team/Bag, Friends, Settings, Revodex, Discussion, Clan
    """

    def __init__(self):
        super().__init__(
            label="submenu_title_text",
            og_resolution=(1920, 1080),
            position=(75, 15),
            size=(610, 75),
            filepath=str(
                BASE_DIR / "assets" / "battle_assets" / "submenu_title_text.png"
            ),
            confidence=0.6,
        )


class MarketTitleText(PymordialImage):
    """Market submenu title region (different position).

    Used by: Market screen only
    """

    def __init__(self):
        super().__init__(
            label="market_title_text",
            og_resolution=(1920, 1080),
            position=(75, 120),
            size=(610, 75),
            filepath=str(
                BASE_DIR / "assets" / "battle_assets" / "market_title_text.png"
            ),
            confidence=0.6,
        )
