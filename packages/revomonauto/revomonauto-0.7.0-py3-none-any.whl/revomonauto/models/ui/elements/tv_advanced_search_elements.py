from pathlib import Path

from pymordial import PymordialImage

tv_advanced_search_button = PymordialImage(
    label="tv_advanced_search_button",
    og_resolution=(1920, 1080),
    filepath=str(
        Path(__file__).parent.parent
        / "assets"
        / "tv_advanced_search_assets"
        / "tv_advanced_search_exit_button.png"
    ),
    confidence=0.8,
)
