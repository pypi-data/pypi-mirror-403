from enum import Enum, auto
from functools import wraps


class GameState(Enum):
    # Login Flow
    NOT_STARTED = auto()
    STARTED = auto()

    # Main Game Loop
    OVERWORLD = auto()  # Walking around, idle
    MAIN_MENU = auto()  # Main menu is open

    # Sub-menus
    MENU_BAG = auto()
    WARDROBE = auto()
    FRIENDS_LIST = auto()
    SETTINGS = auto()
    REVODEX = auto()
    MARKET = auto()
    DISCUSSION = auto()
    CLAN = auto()

    # Battle Flow
    BATTLE = auto()

    # TV
    TV = auto()


class BattleState(Enum):
    # Sub-states for when GameState is BATTLE
    IDLE = auto()
    BAG_OPEN = auto()
    ATTACKS_MENU_OPEN = auto()
    WAITING_FOR_OPPONENT = auto()
    PVP_QUEUE = auto()


def requires_state(*allowed_states):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Resolve game_state from self or self.revomon
            if hasattr(self, "revomon") and hasattr(self.revomon, "game_state"):
                current_state = self.revomon.game_state
            elif hasattr(self, "game_state"):
                current_state = self.game_state
            else:
                self.logger.warning(
                    f"Action {func.__name__} cannot verify state: 'game_state' not found on instance."
                )
                return func(self, *args, **kwargs)

            if current_state not in allowed_states:
                self.logger.warning(
                    f"Action {func.__name__} skipped. Required: {allowed_states}, Current: {current_state}"
                )
                return
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
