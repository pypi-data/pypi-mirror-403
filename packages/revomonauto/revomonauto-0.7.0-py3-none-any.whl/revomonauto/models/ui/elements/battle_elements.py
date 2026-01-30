from pathlib import Path

from pymordial import PymordialImage, PymordialPixel, PymordialText

run_button = PymordialImage(
    label="run_button",
    position=(562, 815),
    size=(200, 230),
    filepath=str(
        Path(__file__).parent.parent / "assets" / "battle_assets" / "run_button.png"
    ),
    confidence=0.6,
    image_text="run",
)

run_button_pixel = PymordialPixel(
    label="run_button_pixel",
    og_resolution=(1920, 1080),
    position=(625, 930),
    pixel_color=(255, 255, 255),
    tolerance=10,
)

# TODO: @dev - need to add run confirm button
# run_confirm_button = PymordialElement()

run_confirm_button_pixel = PymordialPixel(
    label="run_confirm_pixel",
    og_resolution=(1920, 1080),
    position=(1130, 660),
    pixel_color=(255, 255, 255),
    tolerance=10,
)

team_bag_battle_button = PymordialImage(
    label="team_bag_battle_button",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "team_bag_battle_button.png"
    ),
    og_resolution=(1920, 1080),
    position=(862, 815),
    size=(200, 230),
    confidence=0.6,
    image_text="team & bag",
)

team_bag_battle_pixel = PymordialPixel(
    label="team_bag_pixel",
    og_resolution=(1920, 1080),
    position=(957, 930),
    pixel_color=(255, 255, 255),
    tolerance=10,
)

attacks_button = PymordialImage(
    label="attack_button",
    filepath=str(
        Path(__file__).parent.parent / "assets" / "battle_assets" / "attacks_button.png"
    ),
    og_resolution=(1920, 1080),
    position=(1162, 815),
    size=(200, 230),
    confidence=0.6,
    image_text="attacks",
)

attacks_button_pixel = PymordialPixel(
    label="attacks_button_pixel",
    og_resolution=(1920, 1080),
    position=(1260, 925),
    pixel_color=(248, 245, 244),
    tolerance=10,
)

exit_attacks_button = PymordialImage(
    label="exit_attacks_button",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "exit_attacks_button.png"
    ),
    og_resolution=(1920, 1080),
    position=(410, 950),
    size=(90, 90),
    confidence=0.6,
)

exit_attacks_button_pixel = PymordialPixel(
    label="exit_attacks_button_pixel",
    og_resolution=(1920, 1080),
    position=(470, 990),
    pixel_color=(255, 255, 255),
    tolerance=10,
)

player1_mon_name_text = PymordialImage(
    label="player1_mon_name",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_name.png"
    ),
    og_resolution=(1920, 1080),
    position=(0, 45),
    size=(386, 50),
    confidence=0.6,
)

player1_mon_nameplate_pixel = PymordialPixel(
    label="player1_mon_nameplate_pixel",
    og_resolution=(1920, 1080),
    position=(290, 130),
    pixel_color=(0, 199, 155),
    tolerance=10,
)

player1_mon_lvl_text = PymordialImage(
    label="player1_mon_lvl",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_lvl.png"
    ),
    og_resolution=(1920, 1080),
    position=(0, 106),
    size=(126, 40),
    confidence=0.6,
)

player1_mon_hp_img = PymordialImage(
    label="player1_mon_hp",
    filepath=str(
        Path(__file__).parent.parent / "assets" / "battle_assets" / "player1_mon_hp.png"
    ),
    og_resolution=(1920, 1080),
    position=(0, 5),
    size=(410, 43),
    confidence=0.6,
)

player1_mon_move1_button = PymordialImage(
    label="player1_mon_move1",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_move1.png"
    ),
    og_resolution=(1920, 1080),
    position=(554, 800),
    size=(390, 125),
    confidence=0.6,
)

player1_mon_move2_button = PymordialImage(
    label="player1_mon_move2",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_move2.png"
    ),
    og_resolution=(1920, 1080),
    position=(976, 800),
    size=(390, 125),
    confidence=0.6,
)

player1_mon_move3_button = PymordialImage(
    label="player1_mon_move3",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_move3.png"
    ),
    og_resolution=(1920, 1080),
    position=(554, 936),
    size=(390, 125),
    confidence=0.6,
)

player1_mon_move4_button = PymordialImage(
    label="player1_mon_move4",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player1_mon_move4.png"
    ),
    og_resolution=(1920, 1080),
    position=(976, 936),
    size=(390, 125),
    confidence=0.6,
)

player2_mon_name_text = PymordialImage(
    label="player2_mon_name",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player2_mon_name.png"
    ),
    og_resolution=(1920, 1080),
    position=(1534, 45),
    size=(386, 50),
    confidence=0.6,
)

player2_mon_nameplate_pixel = PymordialPixel(
    label="player2_mon_nameplate_pixel",
    og_resolution=(1920, 1080),
    position=(1620, 130),
    pixel_color=(0, 201, 154),
    tolerance=10,
)

player2_mon_lvl_text = PymordialImage(
    label="player2_mon_lvl",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "player2_mon_lvl.png"
    ),
    og_resolution=(1920, 1080),
    position=(1794, 106),
    size=(126, 40),
    confidence=0.6,
)

player2_mon_hp_img = PymordialImage(
    label="player2_mon_hp",
    filepath=str(
        Path(__file__).parent.parent / "assets" / "battle_assets" / "player2_mon_hp.png"
    ),
    og_resolution=(1920, 1080),
    position=(1510, 5),
    size=(410, 43),
    confidence=0.6,
)

waiting_for_opponent_text = PymordialText(
    label="waiting_for_opponent_text",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "waiting_for_opponent_text.png"
    ),
    og_resolution=(1920, 1080),
    position=(577, 906),
    size=(777, 75),
    element_text="Waiting for opponent",
)

run_confirm_button = PymordialImage(
    label="run_confirm_button",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "run_confirm_button.png"
    ),
    og_resolution=(1920, 1080),
    confidence=0.6,
    image_text="yes",
)
run_deny_button = PymordialImage(
    label="run_deny_button",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "run_deny_button.png"
    ),
    og_resolution=(1920, 1080),
    confidence=0.6,
    image_text="no",
)
run_message_text = PymordialImage(
    label="run_message",
    filepath=str(
        Path(__file__).parent.parent / "assets" / "battle_assets" / "run_message.png"
    ),
    og_resolution=(1920, 1080),
    confidence=0.6,
)

battle_log_image = PymordialImage(
    label="battle_log_image",
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "battle_assets"
        / "battle_log_image.png"
    ),
    og_resolution=(1920, 1080),
    position=(1490, 220),
    size=(435, 775),
    confidence=0.6,
)
