from pathlib import Path

from pymordial import PymordialImage, PymordialPixel

BASE_DIR = Path(__file__).parent.parent

clerk_npc_button = PymordialImage(
    label="clerk_npc_button",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "revocenter_assets" / "clerk_npc.png"),
    position=(550, 520),
    size=(75, 120),
    confidence=0.6,
)

clerk_npc_pixel = PymordialPixel(
    label="clerk_npc_pixel",
    og_resolution=(1920, 1080),
    position=(600, 650),
    pixel_color=(62, 128, 195),
    tolerance=10,
)

nurse_npc_button = PymordialImage(
    label="nurse_npc_button",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "revocenter_assets" / "nurse_npc.png"),
    position=(400, 540),
    size=(110, 165),
    confidence=0.6,
)

nurse_npc_pixel = PymordialPixel(
    label="nurse_npc_pixel",
    og_resolution=(1920, 1080),
    position=(545, 645),
    pixel_color=(29, 81, 149),
    tolerance=10,
)

drassius_nurse_npc_pixel = PymordialPixel(
    label="drassius_nurse_npc_pixel",
    og_resolution=(1920, 1080),
    position=(815, 611),
    pixel_color=(93, 46, 111),
    tolerance=10,
)

move_tutor_npc_button = PymordialImage(
    label="move_tutor_npc_button",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "revocenter_assets" / "move_tutor_npc.png"),
    position=(125, 512),
    size=(100, 200),
    confidence=0.6,
)

move_tutor_npc_pixel = PymordialPixel(
    label="move_tutor_npc_pixel",
    og_resolution=(1920, 1080),
    position=(200, 640),
    pixel_color=(67, 136, 201),
    tolerance=10,
)

tv_screen_button = PymordialImage(
    label="tv_screen_button",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "revocenter_assets" / "tv_screen.png"),
    position=(931, 562),
    size=(80, 71),
    confidence=0.7,
)

tv_screen_pixel = PymordialPixel(
    label="tv_screen_pixel",
    og_resolution=(1920, 1080),
    position=(990, 600),
    pixel_color=(14, 20, 28),
    tolerance=10,
)

tv_screen_drassius_button = PymordialImage(
    label="tv_screen_drassius",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "revocenter_assets" / "tv_screen_drassius.png"),
    confidence=0.6,
)


green_sign_pixel = PymordialPixel(
    label="green_sign_pixel",
    og_resolution=(1920, 1080),
    position=(585, 810),
    pixel_color=(92, 166, 127),
    tolerance=15,
)
