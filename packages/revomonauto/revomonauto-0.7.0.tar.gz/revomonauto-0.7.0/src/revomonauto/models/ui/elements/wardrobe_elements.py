from pymordial import PymordialPixel


class ChangeWardrobeTabRightPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_wardrobe_tab_right_pixel",
            og_resolution=(1920, 1080),
            position=(1720, 275),
            pixel_color=(61, 231, 164),
            tolerance=30,
        )


class ChangeWardrobeTabLeftPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_wardrobe_tab_left_pixel",
            og_resolution=(1920, 1080),
            position=(1300, 275),
            pixel_color=(61, 231, 164),
            tolerance=30,
        )


class Item1WearPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="item_1_wear_pixel",
            og_resolution=(1920, 1080),
            position=(1640, 400),
            pixel_color=(143, 114, 168),
            tolerance=10,
        )


class Item2WearPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="item_2_wear_pixel",
            og_resolution=(1920, 1080),
            position=(1640, 510),
            pixel_color=(143, 113, 168),
            tolerance=10,
        )


class Item3WearPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="item_3_wear_pixel",
            og_resolution=(1920, 1080),
            position=(1640, 620),
            pixel_color=(143, 113, 168),
            tolerance=10,
        )


class Item4WearPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="item_4_wear_pixel",
            og_resolution=(1920, 1080),
            position=(1640, 730),
            pixel_color=(143, 113, 168),
            tolerance=10,
        )


class Item5WearPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="item_5_wear_pixel",
            og_resolution=(1920, 1080),
            position=(1640, 840),
            pixel_color=(143, 113, 168),
            tolerance=10,
        )


class ChangeWardrobePageLeftPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_wardrobe_page_left_pixel",
            og_resolution=(1920, 1080),
            position=(1340, 915),
            pixel_color=(64, 231, 166),
            tolerance=10,
        )


class ChangeWardrobePageRightPixel(PymordialPixel):
    def __init__(self):
        super().__init__(
            label="change_wardrobe_page_right_pixel",
            og_resolution=(1920, 1080),
            position=(1650, 915),
            pixel_color=(64, 231, 166),
            tolerance=10,
        )
