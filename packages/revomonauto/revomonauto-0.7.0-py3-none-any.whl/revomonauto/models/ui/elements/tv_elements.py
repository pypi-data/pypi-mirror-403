from pathlib import Path

from pymordial import PymordialElement, PymordialImage

BASE_DIR = Path(__file__).parent.parent

tv_advanced_search_button = PymordialImage(
    label="tv_advanced_search_button",
    og_resolution=(1920, 1080),
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_advanced_search_button.png"),
    position=(145, 115),
    size=(90, 95),
    confidence=0.7,
)

tv_search_input = PymordialImage(
    label="tv_search_input",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_search_input.png"),
    og_resolution=(1920, 1080),
    position=(265, 125),
    size=(430, 65),
    confidence=0.6,
    image_text="search here...",
)

tv_search_button = PymordialImage(
    label="tv_search_button",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_search_button.png"),
    og_resolution=(1920, 1080),
    position=(370, 185),
    size=(215, 60),
    confidence=0.6,
    image_text="search",
)

tv_previous_page_button = PymordialImage(
    label="tv_previous_page_button",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_previous_page_button.png"),
    og_resolution=(1920, 1080),
    position=(780, 120),
    size=(95, 95),
    confidence=0.6,
)

tv_page_number_text = PymordialImage(
    label="tv_page_number_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_page_number_text.png"),
    og_resolution=(1920, 1080),
    position=(880, 130),
    size=(330, 70),
    confidence=0.6,
)

tv_next_page_button = PymordialImage(
    label="tv_next_page_button",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_next_page_button.png"),
    og_resolution=(1920, 1080),
    position=(1220, 120),
    size=(95, 95),
    confidence=0.6,
)

tv_mon_name_text = PymordialImage(
    label="tv_mon_name_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_name_text.png"),
    og_resolution=(1920, 1080),
    position=(1320, 145),
    size=(470, 80),
    confidence=0.6,
)

tv_exit_button = PymordialImage(
    label="tv_exit_button",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_exit_button.png"),
    og_resolution=(1920, 1080),
    position=(1785, 95),
    size=(130, 130),
    confidence=0.6,
)

tv_mon_ability_text = PymordialImage(
    label="tv_mon_ability_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_ability_text.png"),
    og_resolution=(1920, 1080),
    position=(930, 290),
    size=(260, 70),
    confidence=0.6,
)

tv_mon_og_tamer_text = PymordialImage(
    label="tv_mon_og_tamer_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_og_tamer_text.png"),
    og_resolution=(1920, 1080),
    position=(1190, 290),
    size=(220, 70),
    confidence=0.6,
)

tv_mon_nature_text = PymordialImage(
    label="tv_mon_nature_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_nature_text.png"),
    og_resolution=(1920, 1080),
    position=(930, 400),
    size=(255, 55),
    confidence=0.6,
)

tv_mon_exp_text = PymordialImage(
    label="tv_mon_exp_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_exp_text.png"),
    og_resolution=(1920, 1080),
    position=(1190, 400),
    size=(220, 70),
    confidence=0.6,
)

tv_mon_held_item_image = PymordialImage(
    label="tv_mon_held_item_image",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_held_item_image.png"),
    og_resolution=(1920, 1080),
    position=(1795, 220),
    size=(60, 60),
    confidence=0.6,
)

tv_mon_types_image = PymordialImage(
    label="tv_mon_types_image",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_types_image.png"),
    og_resolution=(1920, 1080),
    position=(1760, 525),
    size=(130, 80),
    confidence=0.6,
)

tv_mon_level_text = PymordialImage(
    label="tv_mon_level_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_level_text.png"),
    og_resolution=(1920, 1080),
    position=(1800, 600),
    size=(110, 50),
    confidence=0.6,
)

tv_mon_id_text = PymordialImage(
    label="tv_mon_id_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_id_text.png"),
    og_resolution=(1920, 1080),
    position=(1500, 650),
    size=(400, 50),
    confidence=0.6,
)

tv_mon_hp_stat_text = PymordialImage(
    label="tv_mon_hp_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_hp_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 505),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_hp_iv_text = PymordialImage(
    label="tv_mon_hp_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_hp_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 505),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_hp_ev_text = PymordialImage(
    label="tv_mon_hp_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_hp_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 505),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_atk_stat_text = PymordialImage(
    label="tv_mon_atk_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_atk_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 535),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_atk_iv_text = PymordialImage(
    label="tv_mon_atk_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_atk_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 535),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_atk_ev_text = PymordialImage(
    label="tv_mon_atk_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_atk_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 535),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_def_stat_text = PymordialImage(
    label="tv_mon_def_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_def_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 565),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_def_iv_text = PymordialImage(
    label="tv_mon_def_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_def_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 565),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_def_ev_text = PymordialImage(
    label="tv_mon_def_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_def_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 570),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spa_stat_text = PymordialImage(
    label="tv_mon_spa_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spa_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 595),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spa_iv_text = PymordialImage(
    label="tv_mon_spa_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spa_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 595),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spa_ev_text = PymordialImage(
    label="tv_mon_spa_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spa_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 595),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spd_stat_text = PymordialImage(
    label="tv_mon_spd_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spd_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 625),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spd_iv_text = PymordialImage(
    label="tv_mon_spd_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spd_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 625),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spd_ev_text = PymordialImage(
    label="tv_mon_spd_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spd_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 625),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spe_stat_text = PymordialImage(
    label="tv_mon_spe_stat_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spe_stat_text.png"),
    og_resolution=(1920, 1080),
    position=(1195, 655),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spe_iv_text = PymordialImage(
    label="tv_mon_spe_iv_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spe_iv_text.png"),
    og_resolution=(1920, 1080),
    position=(1270, 655),
    size=(60, 30),
    confidence=0.6,
)

tv_mon_spe_ev_text = PymordialImage(
    label="tv_mon_spe_ev_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_spe_ev_text.png"),
    og_resolution=(1920, 1080),
    position=(1340, 655),
    size=(60, 30),
    confidence=0.6,
)

tv_add_to_party_button = PymordialImage(
    label="tv_add_to_party_button",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_add_to_party_button.png"),
    og_resolution=(1920, 1080),
    position=(990, 700),
    size=(315, 120),
    confidence=0.6,
    image_text="add to party",
)

tv_delete_this_revomon_button = PymordialImage(
    label="tv_delete_this_revomon_button",
    filepath=str(
        BASE_DIR / "assets" / "tv_assets" / "tv_delete_this_revomon_button.png"
    ),
    og_resolution=(1920, 1080),
    position=(990, 825),
    size=(315, 120),
    confidence=0.6,
    image_text="delete this revomon",
)

tv_mon_move1_text = PymordialImage(
    label="tv_mon_move1_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_move1_text.png"),
    og_resolution=(1920, 1080),
    position=(1315, 715),
    size=(250, 50),
    confidence=0.6,
)

tv_mon_move2_text = PymordialImage(
    label="tv_mon_move2_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_move2_text.png"),
    og_resolution=(1920, 1080),
    position=(1315, 770),
    size=(250, 50),
    confidence=0.6,
)

tv_mon_move3_text = PymordialImage(
    label="tv_mon_move3_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_move3_text.png"),
    og_resolution=(1920, 1080),
    position=(1315, 830),
    size=(250, 50),
    confidence=0.6,
)

tv_mon_move4_text = PymordialImage(
    label="tv_mon_move4_text",
    filepath=str(BASE_DIR / "assets" / "tv_assets" / "tv_mon_move4_text.png"),
    og_resolution=(1920, 1080),
    position=(1315, 880),
    size=(250, 50),
    confidence=0.6,
)


def _create_tv_slot_button(slot_number: int, x: int, y: int) -> PymordialElement:
    return PymordialElement(
        label=f"tv_slot{slot_number}_button",
        og_resolution=(1920, 1080),
        position=(x, y),
        size=(145, 135),
    )


tv_slot_buttons: dict[int, PymordialElement] = {}

_start_x = 50
_start_y = 260
_x_increment = 145
_y_increment = 135
_columns = 6
_rows = 5

for _row in range(_rows):
    for _col in range(_columns):
        _slot_num = _row * _columns + _col + 1
        _x_pos = _start_x + (_col * _x_increment)
        _y_pos = _start_y + (_row * _y_increment)
        tv_slot_buttons[_slot_num] = _create_tv_slot_button(_slot_num, _x_pos, _y_pos)
