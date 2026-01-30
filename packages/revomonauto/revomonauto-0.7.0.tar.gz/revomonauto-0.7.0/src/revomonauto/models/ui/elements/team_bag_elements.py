from pathlib import Path

from pymordial import PymordialImage, PymordialPixel

BASE_DIR = Path(__file__).parent.parent

# --- Main Navigation Arrows ---


class ChangeBagTabLeftButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="change_bag_tab_left_button",
            filepath=str(
                BASE_DIR
                / "assets"
                / "team_bag_assets"
                / "change_bag_tab_left_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(20, 205),
            size=(90, 90),
            confidence=0.6,
        )


class ChangeBagTabLeftPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_bag_tab_left_pixel",
            og_resolution=(1920, 1080),
            position=(70, 250),
            pixel_color=(71, 231, 168),
            tolerance=10,
        )


class ChangeBagTabRightButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="change_bag_tab_right_button",
            filepath=str(
                BASE_DIR
                / "assets"
                / "team_bag_assets"
                / "change_bag_tab_right_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(480, 205),
            size=(90, 90),
            confidence=0.6,
        )


class ChangeBagTabRightPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_bag_tab_right_pixel",
            og_resolution=(1920, 1080),
            position=(520, 250),
            pixel_color=(73, 231, 169),
            tolerance=10,
        )


# --- Item Slots (Left Side List) ---


class BagItemSlot1(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_item_slot_1",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_item_slot_1.png"
            ),
            og_resolution=(1920, 1080),
            position=(20, 305),
            size=(290, 50),
            confidence=0.6,
        )


class BagItemSlot2(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_item_slot_2",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_item_slot_2.png"
            ),
            og_resolution=(1920, 1080),
            position=(20, 375),
            size=(290, 50),
            confidence=0.6,
        )


class BagItemSlot3(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_item_slot_3",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_item_slot_3.png"
            ),
            og_resolution=(1920, 1080),
            position=(20, 445),
            size=(290, 50),
            confidence=0.6,
        )


# --- Contextual Action Buttons ---


class BagUseItemButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_use_item_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_use_item_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(235, 315),
            size=(70, 30),
            image_text="use item",
            confidence=0.6,
        )


class BagGiveItemButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_give_item_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_give_item_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(150, 315),
            size=(70, 30),
            image_text="give item",
            confidence=0.6,
        )


# --- Confirmation Popups ---


class BagConfirmYesButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="bag_confirm_yes_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "bag_confirm_yes_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(200, 560),
            size=(80, 40),
            image_text="yes",
            confidence=0.6,
        )


# --- Team Management Buttons (Right Side) ---


class RemoveFromTeamButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="remove_from_team_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "remove_from_team.png"
            ),
            og_resolution=(1920, 1080),
            position=(900, 600),
            size=(85, 85),
            confidence=0.6,
        )


class RemoveFromTeamPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="remove_from_team_pixel",
            og_resolution=(1920, 1080),
            position=(940, 640),
            pixel_color=(241, 76, 76),
            tolerance=10,
        )


class RemoveItemButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="remove_item_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "remove_item_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(900, 330),
            size=(85, 85),
            confidence=0.6,
        )


class RemoveItemPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="remove_item_pixel",
            og_resolution=(1920, 1080),
            position=(940, 370),
            pixel_color=(142, 159, 170),
            tolerance=10,
        )


class SetFirstButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="set_first_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "set_first_button.png"
            ),
            og_resolution=(1920, 1080),
            position=(900, 460),
            size=(85, 85),
            confidence=0.6,
        )


class SetFirstPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="set_first_pixel",
            og_resolution=(1920, 1080),
            position=(940, 500),
            pixel_color=(203, 181, 73),
            tolerance=10,
        )


class SendToBattleButton(PymordialImage):
    def __init__(self):
        super().__init__(
            label="send_to_battle_button",
            filepath=str(
                BASE_DIR / "assets" / "team_bag_assets" / "send_to_battle_button.png"
            ),
            og_resolution=(1920, 1080),
            confidence=0.6,
            image_text="send to battle",
        )


class SendToBattlePixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="send_to_battle_pixel",
            og_resolution=(1920, 1080),
            position=(940, 500),
            pixel_color=(203, 181, 73),
            tolerance=10,
        )


class NoItemEquippedPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="no_item_equipped_pixel",
            og_resolution=(1920, 1080),
            position=(900, 350),
            pixel_color=(255, 255, 255),
            tolerance=10,
        )
