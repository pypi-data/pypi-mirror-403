from pymordial import PymordialPixel


# ---- Shared ----
class GenericInsiderevocenterPixel1(PymordialPixel):
    """Location signature pixel 1 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(54, 158, 247),
            tolerance=20,
        )


class GenericInsiderevocenterPixel2(PymordialPixel):
    """Location signature pixel 2 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(55, 159, 250),
            tolerance=20,
        )


class GenericInsiderevocenterPixel3(PymordialPixel):
    """Location signature pixel 3 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(55, 159, 250),
            tolerance=20,
        )


class GenericInsiderevocenterPixel4(PymordialPixel):
    """Location signature pixel 4 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(55, 159, 250),
            tolerance=20,
        )


class GenericInsiderevocenterPixel5(PymordialPixel):
    """Location signature pixel 5 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(203, 92, 70),
            tolerance=20,
        )


class GenericInsiderevocenterPixel6(PymordialPixel):
    """Location signature pixel 6 for generic - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="generic_insiderevocenter_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(227, 228, 231),
            tolerance=20,
        )


# Location signature for generic - insiderevocenter (any time)
GENERIC_INSIDEREVOCENTER_SIGNATURE = (
    GenericInsiderevocenterPixel1(),
    GenericInsiderevocenterPixel2(),
    GenericInsiderevocenterPixel3(),
    GenericInsiderevocenterPixel4(),
    GenericInsiderevocenterPixel5(),
    GenericInsiderevocenterPixel6(),
)


# ---- Drassius City ----
class DrassiuscityInsiderevocenterPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(108, 76, 50),
            tolerance=20,
        )


class DrassiuscityInsiderevocenterPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(109, 77, 51),
            tolerance=20,
        )


class DrassiuscityInsiderevocenterPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(93, 67, 40),
            tolerance=20,
        )


class DrassiuscityInsiderevocenterPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(149, 147, 137),
            tolerance=20,
        )


class DrassiuscityInsiderevocenterPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(149, 147, 137),
            tolerance=20,
        )


class DrassiuscityInsiderevocenterPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - insiderevocenter (any time)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_insiderevocenter_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(154, 152, 144),
            tolerance=20,
        )


# Location signature for drassiuscity - insiderevocenter (any time)
DRASSIUSCITY_INSIDEREVOCENTER_SIGNATURE = (
    DrassiuscityInsiderevocenterPixel1(),
    DrassiuscityInsiderevocenterPixel2(),
    DrassiuscityInsiderevocenterPixel3(),
    DrassiuscityInsiderevocenterPixel4(),
    DrassiuscityInsiderevocenterPixel5(),
    DrassiuscityInsiderevocenterPixel6(),
)


# ---- Morning Cycle ----
class DrassiuscityOutsiderevocenterMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(172, 139, 189),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(177, 144, 192),
            tolerance=20,
        )


# Location signature for drassiuscity - outsiderevocenter (morning)
DRASSIUSCITY_OUTSIDEREVOCENTER_MORNING_SIGNATURE = (
    DrassiuscityOutsiderevocenterMorningPixel1(),
    DrassiuscityOutsiderevocenterMorningPixel2(),
    DrassiuscityOutsiderevocenterMorningPixel3(),
    DrassiuscityOutsiderevocenterMorningPixel4(),
    DrassiuscityOutsiderevocenterMorningPixel5(),
    DrassiuscityOutsiderevocenterMorningPixel6(),
)


class DrassiuscityVictoryislandportalMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - victoryislandportal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


# Location signature for drassiuscity - victoryislandportal (morning)
DRASSIUSCITY_VICTORYISLANDPORTAL_MORNING_SIGNATURE = (
    DrassiuscityVictoryislandportalMorningPixel1(),
    DrassiuscityVictoryislandportalMorningPixel2(),
    DrassiuscityVictoryislandportalMorningPixel3(),
    DrassiuscityVictoryislandportalMorningPixel4(),
    DrassiuscityVictoryislandportalMorningPixel5(),
    DrassiuscityVictoryislandportalMorningPixel6(),
)


class DrassiuscityRoute1portalMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(188, 147, 185),
            tolerance=20,
        )


class DrassiuscityRoute1portalMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(185, 144, 189),
            tolerance=20,
        )


class DrassiuscityRoute1portalMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(184, 149, 189),
            tolerance=20,
        )


class DrassiuscityRoute1portalMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(182, 149, 190),
            tolerance=20,
        )


class DrassiuscityRoute1portalMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(183, 146, 191),
            tolerance=20,
        )


class DrassiuscityRoute1portalMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - route1portal (morning)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(180, 150, 188),
            tolerance=20,
        )


# Location signature for drassiuscity - route1portal (morning)
DRASSIUSCITY_ROUTE1PORTAL_MORNING_SIGNATURE = (
    DrassiuscityRoute1portalMorningPixel1(),
    DrassiuscityRoute1portalMorningPixel2(),
    DrassiuscityRoute1portalMorningPixel3(),
    DrassiuscityRoute1portalMorningPixel4(),
    DrassiuscityRoute1portalMorningPixel5(),
    DrassiuscityRoute1portalMorningPixel6(),
)


# ---- Afternoon Cycle ----
class DrassiuscityOutsiderevocenterAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class DrassiuscityOutsiderevocenterAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class DrassiuscityOutsiderevocenterAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityOutsiderevocenterAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class DrassiuscityOutsiderevocenterAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityOutsiderevocenterAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for drassiuscity - outsiderevocenter (afternoon)
DRASSIUSCITY_OUTSIDEREVOCENTER_AFTERNOON_SIGNATURE = (
    DrassiuscityOutsiderevocenterAfternoonPixel1(),
    DrassiuscityOutsiderevocenterAfternoonPixel2(),
    DrassiuscityOutsiderevocenterAfternoonPixel3(),
    DrassiuscityOutsiderevocenterAfternoonPixel4(),
    DrassiuscityOutsiderevocenterAfternoonPixel5(),
    DrassiuscityOutsiderevocenterAfternoonPixel6(),
)


class DrassiuscityVictoryislandportalAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class DrassiuscityVictoryislandportalAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class DrassiuscityVictoryislandportalAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityVictoryislandportalAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class DrassiuscityVictoryislandportalAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityVictoryislandportalAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - victoryislandportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for drassiuscity - victoryislandportal (afternoon)
DRASSIUSCITY_VICTORYISLANDPORTAL_AFTERNOON_SIGNATURE = (
    DrassiuscityVictoryislandportalAfternoonPixel1(),
    DrassiuscityVictoryislandportalAfternoonPixel2(),
    DrassiuscityVictoryislandportalAfternoonPixel3(),
    DrassiuscityVictoryislandportalAfternoonPixel4(),
    DrassiuscityVictoryislandportalAfternoonPixel5(),
    DrassiuscityVictoryislandportalAfternoonPixel6(),
)


class DrassiuscityRoute1portalAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class DrassiuscityRoute1portalAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class DrassiuscityRoute1portalAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityRoute1portalAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class DrassiuscityRoute1portalAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class DrassiuscityRoute1portalAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - route1portal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for drassiuscity - route1portal (afternoon)
DRASSIUSCITY_ROUTE1PORTAL_AFTERNOON_SIGNATURE = (
    DrassiuscityRoute1portalAfternoonPixel1(),
    DrassiuscityRoute1portalAfternoonPixel2(),
    DrassiuscityRoute1portalAfternoonPixel3(),
    DrassiuscityRoute1portalAfternoonPixel4(),
    DrassiuscityRoute1portalAfternoonPixel5(),
    DrassiuscityRoute1portalAfternoonPixel6(),
)


# ---- Night Cycle ----
class DrassiuscityOutsiderevocenterNightPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterNightPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterNightPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterNightPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterNightPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityOutsiderevocenterNightPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_outsiderevocenter_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(92, 46, 110),
            tolerance=20,
        )


# Location signature for drassiuscity - outsiderevocenter (night)
DRASSIUSCITY_OUTSIDEREVOCENTER_NIGHT_SIGNATURE = (
    DrassiuscityOutsiderevocenterNightPixel1(),
    DrassiuscityOutsiderevocenterNightPixel2(),
    DrassiuscityOutsiderevocenterNightPixel3(),
    DrassiuscityOutsiderevocenterNightPixel4(),
    DrassiuscityOutsiderevocenterNightPixel5(),
    DrassiuscityOutsiderevocenterNightPixel6(),
)


class DrassiuscityVictoryislandportalNightPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalNightPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalNightPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalNightPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalNightPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


class DrassiuscityVictoryislandportalNightPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - victoryislandportal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_victoryislandportal_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(255, 255, 255),
            tolerance=20,
        )


# Location signature for drassiuscity - victoryislandportal (night)
DRASSIUSCITY_VICTORYISLANDPORTAL_NIGHT_SIGNATURE = (
    DrassiuscityVictoryislandportalNightPixel1(),
    DrassiuscityVictoryislandportalNightPixel2(),
    DrassiuscityVictoryislandportalNightPixel3(),
    DrassiuscityVictoryislandportalNightPixel4(),
    DrassiuscityVictoryislandportalNightPixel5(),
    DrassiuscityVictoryislandportalNightPixel6(),
)


class DrassiuscityRoute1portalNightPixel1(PymordialPixel):
    """Location signature pixel 1 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityRoute1portalNightPixel2(PymordialPixel):
    """Location signature pixel 2 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityRoute1portalNightPixel3(PymordialPixel):
    """Location signature pixel 3 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityRoute1portalNightPixel4(PymordialPixel):
    """Location signature pixel 4 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityRoute1portalNightPixel5(PymordialPixel):
    """Location signature pixel 5 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class DrassiuscityRoute1portalNightPixel6(PymordialPixel):
    """Location signature pixel 6 for drassiuscity - route1portal (night)."""

    def __init__(self):
        super().__init__(
            label="drassiuscity_route1portal_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(88, 46, 107),
            tolerance=20,
        )


# Location signature for drassiuscity - route1portal (night)
DRASSIUSCITY_ROUTE1PORTAL_NIGHT_SIGNATURE = (
    DrassiuscityRoute1portalNightPixel1(),
    DrassiuscityRoute1portalNightPixel2(),
    DrassiuscityRoute1portalNightPixel3(),
    DrassiuscityRoute1portalNightPixel4(),
    DrassiuscityRoute1portalNightPixel5(),
    DrassiuscityRoute1portalNightPixel6(),
)


# ---- Victory Island ----
# ---- Morning Cycle ----
class VictoryislandOutsiderevocenterMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(172, 139, 189),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - outsiderevocenter (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(177, 144, 192),
            tolerance=20,
        )


# Location signature for victoryisland - outsiderevocenter (morning)
VICTORYISLAND_OUTSIDEREVOCENTER_MORNING_SIGNATURE = (
    VictoryislandOutsiderevocenterMorningPixel1(),
    VictoryislandOutsiderevocenterMorningPixel2(),
    VictoryislandOutsiderevocenterMorningPixel3(),
    VictoryislandOutsiderevocenterMorningPixel4(),
    VictoryislandOutsiderevocenterMorningPixel5(),
    VictoryislandOutsiderevocenterMorningPixel6(),
)


class VictoryislandDrassiuscityportalMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(185, 249, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(182, 239, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(177, 235, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(168, 228, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(151, 213, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(152, 207, 255),
            tolerance=20,
        )


# Location signature for victoryisland - drassiuscityportal (morning)
VICTORYISLAND_DRASSIUSCITYPORTAL_MORNING_SIGNATURE = (
    VictoryislandDrassiuscityportalMorningPixel1(),
    VictoryislandDrassiuscityportalMorningPixel2(),
    VictoryislandDrassiuscityportalMorningPixel3(),
    VictoryislandDrassiuscityportalMorningPixel4(),
    VictoryislandDrassiuscityportalMorningPixel5(),
    VictoryislandDrassiuscityportalMorningPixel6(),
)


# ---- Afternoon Cycle ----
class VictoryislandOutsiderevocenterAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class VictoryislandOutsiderevocenterAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class VictoryislandOutsiderevocenterAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class VictoryislandOutsiderevocenterAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class VictoryislandOutsiderevocenterAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class VictoryislandOutsiderevocenterAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - outsiderevocenter (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for victoryisland - outsiderevocenter (afternoon)
VICTORYISLAND_OUTSIDEREVOCENTER_AFTERNOON_SIGNATURE = (
    VictoryislandOutsiderevocenterAfternoonPixel1(),
    VictoryislandOutsiderevocenterAfternoonPixel2(),
    VictoryislandOutsiderevocenterAfternoonPixel3(),
    VictoryislandOutsiderevocenterAfternoonPixel4(),
    VictoryislandOutsiderevocenterAfternoonPixel5(),
    VictoryislandOutsiderevocenterAfternoonPixel6(),
)


class VictoryislandDrassiuscityportalAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class VictoryislandDrassiuscityportalAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class VictoryislandDrassiuscityportalAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class VictoryislandDrassiuscityportalAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class VictoryislandDrassiuscityportalAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class VictoryislandDrassiuscityportalAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for victoryisland - drassiuscityportal (afternoon)
VICTORYISLAND_DRASSIUSCITYPORTAL_AFTERNOON_SIGNATURE = (
    VictoryislandDrassiuscityportalAfternoonPixel1(),
    VictoryislandDrassiuscityportalAfternoonPixel2(),
    VictoryislandDrassiuscityportalAfternoonPixel3(),
    VictoryislandDrassiuscityportalAfternoonPixel4(),
    VictoryislandDrassiuscityportalAfternoonPixel5(),
    VictoryislandDrassiuscityportalAfternoonPixel6(),
)


# ---- Night Cycle ----
class VictoryislandOutsiderevocenterNightPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterNightPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterNightPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterNightPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterNightPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class VictoryislandOutsiderevocenterNightPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - outsiderevocenter (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_outsiderevocenter_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(92, 46, 110),
            tolerance=20,
        )


# Location signature for victoryisland - outsiderevocenter (night)
VICTORYISLAND_OUTSIDEREVOCENTER_NIGHT_SIGNATURE = (
    VictoryislandOutsiderevocenterNightPixel1(),
    VictoryislandOutsiderevocenterNightPixel2(),
    VictoryislandOutsiderevocenterNightPixel3(),
    VictoryislandOutsiderevocenterNightPixel4(),
    VictoryislandOutsiderevocenterNightPixel5(),
    VictoryislandOutsiderevocenterNightPixel6(),
)


class VictoryislandDrassiuscityportalNightPixel1(PymordialPixel):
    """Location signature pixel 1 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(180, 242, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalNightPixel2(PymordialPixel):
    """Location signature pixel 2 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(174, 234, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalNightPixel3(PymordialPixel):
    """Location signature pixel 3 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(178, 233, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalNightPixel4(PymordialPixel):
    """Location signature pixel 4 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(173, 233, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalNightPixel5(PymordialPixel):
    """Location signature pixel 5 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(158, 222, 255),
            tolerance=20,
        )


class VictoryislandDrassiuscityportalNightPixel6(PymordialPixel):
    """Location signature pixel 6 for victoryisland - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="victoryisland_drassiuscityportal_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(132, 201, 255),
            tolerance=20,
        )


# Location signature for victoryisland - drassiuscityportal (night)
VICTORYISLAND_DRASSIUSCITYPORTAL_NIGHT_SIGNATURE = (
    VictoryislandDrassiuscityportalNightPixel1(),
    VictoryislandDrassiuscityportalNightPixel2(),
    VictoryislandDrassiuscityportalNightPixel3(),
    VictoryislandDrassiuscityportalNightPixel4(),
    VictoryislandDrassiuscityportalNightPixel5(),
    VictoryislandDrassiuscityportalNightPixel6(),
)


# ---- Route 1 ----
# ---- Morning Cycle ----
class Route1DrassiuscityportalMorningPixel1(PymordialPixel):
    """Location signature pixel 1 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(172, 140, 189),
            tolerance=20,
        )


class Route1DrassiuscityportalMorningPixel2(PymordialPixel):
    """Location signature pixel 2 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(172, 139, 189),
            tolerance=20,
        )


class Route1DrassiuscityportalMorningPixel3(PymordialPixel):
    """Location signature pixel 3 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class Route1DrassiuscityportalMorningPixel4(PymordialPixel):
    """Location signature pixel 4 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class Route1DrassiuscityportalMorningPixel5(PymordialPixel):
    """Location signature pixel 5 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(173, 141, 189),
            tolerance=20,
        )


class Route1DrassiuscityportalMorningPixel6(PymordialPixel):
    """Location signature pixel 6 for route1 - drassiuscityportal (morning)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_morning_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(177, 144, 192),
            tolerance=20,
        )


# Location signature for route1 - drassiuscityportal (morning)
ROUTE1_DRASSIUSCITYPORTAL_MORNING_SIGNATURE = (
    Route1DrassiuscityportalMorningPixel1(),
    Route1DrassiuscityportalMorningPixel2(),
    Route1DrassiuscityportalMorningPixel3(),
    Route1DrassiuscityportalMorningPixel4(),
    Route1DrassiuscityportalMorningPixel5(),
    Route1DrassiuscityportalMorningPixel6(),
)


# ---- Afternoon Cycle ----
class Route1DrassiuscityportalAfternoonPixel1(PymordialPixel):
    """Location signature pixel 1 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(139, 184, 240),
            tolerance=10,
        )


class Route1DrassiuscityportalAfternoonPixel2(PymordialPixel):
    """Location signature pixel 2 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(138, 185, 240),
            tolerance=10,
        )


class Route1DrassiuscityportalAfternoonPixel3(PymordialPixel):
    """Location signature pixel 3 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class Route1DrassiuscityportalAfternoonPixel4(PymordialPixel):
    """Location signature pixel 4 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(140, 188, 240),
            tolerance=10,
        )


class Route1DrassiuscityportalAfternoonPixel5(PymordialPixel):
    """Location signature pixel 5 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


class Route1DrassiuscityportalAfternoonPixel6(PymordialPixel):
    """Location signature pixel 6 for route1 - drassiuscityportal (afternoon)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_afternoon_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(141, 187, 240),
            tolerance=10,
        )


# Location signature for route1 - drassiuscityportal (afternoon)
ROUTE1_DRASSIUSCITYPORTAL_AFTERNOON_SIGNATURE = (
    Route1DrassiuscityportalAfternoonPixel1(),
    Route1DrassiuscityportalAfternoonPixel2(),
    Route1DrassiuscityportalAfternoonPixel3(),
    Route1DrassiuscityportalAfternoonPixel4(),
    Route1DrassiuscityportalAfternoonPixel5(),
    Route1DrassiuscityportalAfternoonPixel6(),
)


# ---- Night Cycle ----
class Route1DrassiuscityportalNightPixel1(PymordialPixel):
    """Location signature pixel 1 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel1",
            og_resolution=(1920, 1080),
            position=(1480, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class Route1DrassiuscityportalNightPixel2(PymordialPixel):
    """Location signature pixel 2 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel2",
            og_resolution=(1920, 1080),
            position=(1504, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class Route1DrassiuscityportalNightPixel3(PymordialPixel):
    """Location signature pixel 3 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel3",
            og_resolution=(1920, 1080),
            position=(1528, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class Route1DrassiuscityportalNightPixel4(PymordialPixel):
    """Location signature pixel 4 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel4",
            og_resolution=(1920, 1080),
            position=(1552, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class Route1DrassiuscityportalNightPixel5(PymordialPixel):
    """Location signature pixel 5 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel5",
            og_resolution=(1920, 1080),
            position=(1576, 320),
            pixel_color=(90, 46, 110),
            tolerance=20,
        )


class Route1DrassiuscityportalNightPixel6(PymordialPixel):
    """Location signature pixel 6 for route1 - drassiuscityportal (night)."""

    def __init__(self):
        super().__init__(
            label="route1_drassiuscityportal_night_pixel6",
            og_resolution=(1920, 1080),
            position=(1600, 320),
            pixel_color=(91, 46, 110),
            tolerance=20,
        )


# Location signature for route1 - drassiuscityportal (night)
ROUTE1_DRASSIUSCITYPORTAL_NIGHT_SIGNATURE = (
    Route1DrassiuscityportalNightPixel1(),
    Route1DrassiuscityportalNightPixel2(),
    Route1DrassiuscityportalNightPixel3(),
    Route1DrassiuscityportalNightPixel4(),
    Route1DrassiuscityportalNightPixel5(),
    Route1DrassiuscityportalNightPixel6(),
)
