from pathlib import Path

from pymordial import PymordialImage, PymordialPixel


class TamerNameText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="tamer_name_text",
            og_resolution=(1920, 1080),
            position=(60, 15),
            size=(1150, 80),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "tamer_name_text.png"
            ),
            confidence=0.6,
        )


class TamerSelfieImg(PymordialImage):
    def __init__(self):
        super().__init__(
            label="tamer_selfie_img",
            og_resolution=(1920, 1080),
            position=(30, 110),
            size=(375, 375),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "tamer_selfie_img.png"
            ),
            confidence=0.6,
        )


class WardrobeButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="wardrobe_button",
            og_resolution=(1920, 1080),
            position=(580, 205),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "wardrobe_button.png"
            ),
            confidence=0.8,
            image_text="wardrobe",
        )


class TeamBagMenuButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="team_bag_menu_button",
            og_resolution=(1920, 1080),
            position=(780, 205),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "team_bag_menu_button.png"
            ),
            confidence=0.8,
            image_text="team/bag",
        )


class RecallButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="recall_button",
            og_resolution=(1920, 1080),
            position=(980, 205),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "recall_button.png"
            ),
            confidence=0.8,
            image_text="recall",
        )


class FriendsButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="friends_button",
            og_resolution=(1920, 1080),
            position=(1180, 205),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "friends_button.png"
            ),
            confidence=0.8,
            image_text="friends",
        )


class SettingsButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="settings_button",
            og_resolution=(1920, 1080),
            position=(580, 415),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "settings_button.png"
            ),
            confidence=0.8,
            image_text="settings",
        )


class RevodexButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="revodex_button",
            og_resolution=(1920, 1080),
            position=(780, 415),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "revodex_button.png"
            ),
            confidence=0.8,
            image_text="revodex",
        )


class MarketButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="market_button",
            og_resolution=(1920, 1080),
            position=(980, 415),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "market_button.png"
            ),
            confidence=0.8,
            image_text="market",
        )


class DiscussionButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="discussion_button",
            og_resolution=(1920, 1080),
            position=(1180, 415),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "discussion_button.png"
            ),
            confidence=0.8,
            image_text="discussion",
        )


class PvpButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="pvp_button",
            og_resolution=(1920, 1080),
            position=(580, 625),
            size=(200, 210),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "pvp_button.png"
            ),
            confidence=0.8,
            image_text="pvp",
        )


class ClanButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="clan_button",
            og_resolution=(1920, 1080),
            position=(780, 650),
            size=(200, 50),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "clan_button.png"
            ),
            confidence=0.8,
            image_text="clan",
        )


class GameWalletText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="game_wallet_text",
            og_resolution=(1920, 1080),
            position=(40, 730),
            size=(530, 50),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "game_wallet_text.png"
            ),
            confidence=0.6,
        )


class RevomonSeenText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="revomon_seen_text",
            og_resolution=(1920, 1080),
            position=(300, 805),
            size=(170, 50),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "revomon_seen_text.png"
            ),
            confidence=0.6,
        )


class PvpRatingText(PymordialImage):
    def __init__(self):
        super().__init__(
            label="pvp_rating_text",
            og_resolution=(1920, 1080),
            position=(300, 880),
            size=(170, 50),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "pvp_rating_text.png"
            ),
            confidence=0.6,
        )


class ResetPositionButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="reset_position_button",
            og_resolution=(1920, 1080),
            position=(785, 870),
            size=(360, 70),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "reset_position_button.png"
            ),
            confidence=0.8,
            image_text="reset my position",
        )


class QuitGameButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="quit_game_button",
            og_resolution=(1920, 1080),
            filepath=str(
                Path(__file__).parent.parent
                / "assets"
                / "main_menu_assets"
                / "quit_game_button.png"
            ),
            position=(30, 980),
            size=(180, 80),
            confidence=0.8,
        )


class QuitGamePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="quit_game_pixel",
            og_resolution=(1920, 1080),
            position=(120, 1001),
            pixel_color=(247, 99, 99),
            tolerance=10,
        )


# =============================================================================
# PVP Queue Loading Circle Pixels
# =============================================================================


class PvpLoadingPixelTop(PymordialPixel):
    """Top loading circle pixel for PVP queue detection."""

    def __init__(self):
        super().__init__(
            label="pvp_loading_pixel_top",
            og_resolution=(1920, 1080),
            position=(690, 665),
            pixel_color=(200, 230, 242),  # Midpoint between lightest/darkest
            tolerance=60,  # Wide tolerance for animation
        )


class PvpLoadingPixelRight(PymordialPixel):
    """Right loading circle pixel for PVP queue detection."""

    def __init__(self):
        super().__init__(
            label="pvp_loading_pixel_right",
            og_resolution=(1920, 1080),
            position=(765, 730),
            pixel_color=(200, 230, 242),
            tolerance=60,
        )


class PvpLoadingPixelBottom(PymordialPixel):
    """Bottom loading circle pixel for PVP queue detection."""

    def __init__(self):
        super().__init__(
            label="pvp_loading_pixel_bottom",
            og_resolution=(1920, 1080),
            position=(690, 795),
            pixel_color=(200, 230, 242),
            tolerance=60,
        )


class PvpLoadingPixelLeft(PymordialPixel):
    """Left loading circle pixel for PVP queue detection."""

    def __init__(self):
        super().__init__(
            label="pvp_loading_pixel_left",
            og_resolution=(1920, 1080),
            position=(620, 730),
            pixel_color=(200, 230, 242),
            tolerance=60,
        )
