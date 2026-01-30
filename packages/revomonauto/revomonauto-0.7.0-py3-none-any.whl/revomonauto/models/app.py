import logging

from pymordial.core.state_machine import AppState
from pymordialblue.android_app import PymordialAndroidApp

from .action import Actions
from .action_handlers import (
    CustomHandler,
    NoWaitHandler,
    ScreenTransitionHandler,
    StateUpdateHandler,
)
from .action_registry import ActionRegistry
from .states import BattleState, GameState
from .ui.screens.battle_screen import BattleScreen
from .ui.screens.clan_screen import ClanScreen
from .ui.screens.discussion_screen import DiscussionScreen
from .ui.screens.friends_list_screen import FriendsListScreen
from .ui.screens.login_screen import LoginScreen
from .ui.screens.main_menu_screen import MainMenuScreen
from .ui.screens.market_screen import MarketScreen
from .ui.screens.overworld_screen import OverworldScreen
from .ui.screens.pvp_queue_screen import PvpQueueScreen
from .ui.screens.revocenter_screen import RevocenterScreen
from .ui.screens.revodex_screen import RevodexScreen
from .ui.screens.settings_screen import SettingsScreen
from .ui.screens.shared_screen import SharedScreen
from .ui.screens.start_game_screen import StartGameScreen
from .ui.screens.team_bag_screen import TeamBagScreen
from .ui.screens.tv_advanced_search_screen import TvAdvancedSearchScreen
from .ui.screens.tv_screen import TvScreen
from .ui.screens.wardrobe_screen import WardrobeScreen


class RevomonApp(PymordialAndroidApp):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing RevomonApp...")

        # Initialize Screens
        screens = {
            "shared": SharedScreen(),
            "start_game": StartGameScreen(),
            "login": LoginScreen(),
            "overworld": OverworldScreen(),
            "main_menu": MainMenuScreen(),
            "battle": BattleScreen(),
            "friends_list": FriendsListScreen(),
            "settings": SettingsScreen(),
            "revodex": RevodexScreen(),
            "market": MarketScreen(),
            "discussion": DiscussionScreen(),
            "clan": ClanScreen(),
            "pvp_queue": PvpQueueScreen(),
            "team_bag": TeamBagScreen(),
            "revocenter": RevocenterScreen(),
            "tv": TvScreen(),
            "tv_advanced_search": TvAdvancedSearchScreen(),
            "wardrobe": WardrobeScreen(),
        }

        super().__init__(
            app_name="revomon",
            package_name="com.revomon.vr",
            screens=screens,
        )

        self.last_action = None
        self.actions = Actions()

        self.game_state = GameState.NOT_STARTED
        self.battle_sub_state = BattleState.IDLE

        # Remaining attributes that don't fit into state machines
        self.auto_run: bool = False
        self.auto_battle: bool = True
        self.curr_screen: str | None = None
        self.is_mon_recalled = True
        self.tv_current_page = 1
        self.tv_max_slots = 30
        self.tv_slot_selected = 0
        self.tv_searching_for = None
        self.tv_slot_selected_attribs = None
        self.is_grading = False
        self.is_mons_graded = False

        self.current_bag_tab = "misc"
        self.current_bag_page = 1
        self.current_wardrobe_tab = "head"
        self.current_wardrobe_page = 1

        self.current_city = "drassiuscity"
        self.current_location = "insiderevocenter"

        self.mon_details_img = None
        self.mon_detail_imgs = None

        self.team = None
        self.mon_on_field = {
            "name": None,
            "level": None,
            "current_hp_percentage": None,
            "current_hp": None,
            "max_hp": None,
            "ability": None,
            "nature": None,
            "moves": [
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
            ],
        }
        self.last_move_used = None

        self.opps_team = None
        self.opps_mon_on_field = {
            "name": None,
            "level": None,
            "current_hp_percentage": None,
            "current_hp": None,
            "max_hp": None,
            "ability": None,
            "nature": None,
            "moves": [
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
                {"name": None, "type": None, "pp": {"current": None, "total": None}},
            ],
        }
        self.opps_last_move_used = None

        # Initialize action registry and register handlers
        self.action_registry = ActionRegistry()
        self._register_action_handlers()

        self.logger.info("RevomonApp initialized successfully.")

    def _register_action_handlers(self) -> None:
        """Register all action handlers with the registry."""
        registry = self.action_registry

        # ===== No-Wait Actions =====
        for action_name in [
            "move",
            "perform_idle_sequence",
            "execute_movement_script",
            "toggle_auto_run",
            "toggle_auto_battle",
            "go_to_wardrobe_tab",
            "go_to_bag_tab",
            "select_tv_slot",
            "tv_next_page",
            "tv_prev_page",
        ]:
            registry.register(action_name, NoWaitHandler(action_name))

        # ===== State Update Actions =====
        registry.register(
            "enter_pvp_queue",
            ScreenTransitionHandler(
                expected_screens=["pvp_queue"],
                fallback_screens=["main_menu"],
            ),
        )
        registry.register(
            "exit_pvp_queue",
            ScreenTransitionHandler(
                expected_screens=["main_menu"],
                fallback_screens=["pvp_queue"],
            ),
        )
        registry.register(
            "recall_revomon",
            StateUpdateHandler(state_updates={"is_mon_recalled": True}),
        )
        registry.register(
            "choose_move", StateUpdateHandler(state_updates={"last_move_used": None})
        )
        registry.register(
            "tv_select_revomon",
            StateUpdateHandler(state_updates={"tv_slot_selected": 1}),
        )

        # ===== Screen Transition Actions =====
        registry.register(
            "open_revomon_app", ScreenTransitionHandler(expected_screens=["start_game"])
        )
        registry.register(
            "start_game", ScreenTransitionHandler(expected_screens=["login"])
        )
        registry.register(
            "login",
            ScreenTransitionHandler(
                expected_screens=["overworld"], fallback_screens=["battle"]
            ),
        )
        registry.register(
            "open_main_menu",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_main_menu",
            ScreenTransitionHandler(
                expected_screens=["overworld"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_attacks_menu",
            ScreenTransitionHandler(
                expected_screens=["attacks_menu"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "close_attacks_menu",
            ScreenTransitionHandler(
                expected_screens=["battle"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "open_menu_bag",
            ScreenTransitionHandler(
                expected_screens=["team_bag"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_menu_bag",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_battle_bag",
            ScreenTransitionHandler(
                expected_screens=["team_bag"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "close_battle_bag",
            ScreenTransitionHandler(
                expected_screens=["battle"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "open_available_bag",
            ScreenTransitionHandler(
                expected_screens=["team_bag"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_available_bag",
            ScreenTransitionHandler(
                expected_screens=["main_menu", "battle"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "open_wardrobe", ScreenTransitionHandler(expected_screens=["wardrobe"])
        )

        registry.register(
            "close_wardrobe",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_friends_list",
            ScreenTransitionHandler(
                expected_screens=["friends_list"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_friends_list",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_settings",
            ScreenTransitionHandler(
                expected_screens=["settings"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_settings",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_revodex",
            ScreenTransitionHandler(
                expected_screens=["revodex"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_revodex",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_market",
            ScreenTransitionHandler(
                expected_screens=["market"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_market",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_discussion",
            ScreenTransitionHandler(
                expected_screens=["discussion"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_discussion",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_clan",
            ScreenTransitionHandler(
                expected_screens=["clan"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_clan",
            ScreenTransitionHandler(
                expected_screens=["main_menu"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "open_tv",
            ScreenTransitionHandler(
                expected_screens=["tv"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "close_tv",
            ScreenTransitionHandler(
                expected_screens=["overworld"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "tv_search_for_revomon",
            ScreenTransitionHandler(
                expected_screens=["tv"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "throw_ball",
            ScreenTransitionHandler(
                expected_screens=["battle", "overworld"], fallback_screens=["login"]
            ),
        )
        registry.register(
            "run_from_battle",
            ScreenTransitionHandler(
                expected_screens=["overworld"], fallback_screens=["battle", "login"]
            ),
        )
        registry.register(
            "reset_position",
            ScreenTransitionHandler(
                expected_screens=["overworld"], fallback_screens=["battle", "login"]
            ),
        )

        # ===== Custom Actions =====
        registry.register("close_revomon_app", CustomHandler(self._verify_app_closed))
        registry.register("quit_game", CustomHandler(self._verify_app_closed))

        self.logger.info(f"Registered {len(registry)} action handlers")

    def _verify_app_closed(self, timeout: int) -> bool:
        """Custom handler for close_revomon_app action.

        Note: The close_app() method already verified the app is closed via
        multiple ps checks. This handler just updates the internal state.
        """
        # close_app() in core_lifecycle already called self.close() which
        # used adb.close_app() - that method polls is_app_running internally
        # and only returns True if the app is confirmed closed.
        # So we just need to do a quick sanity check and update state.
        try:
            # Quick single check (no retries to avoid long timeouts)
            assert self.pymordial_controller is not None
            if not self.pymordial_controller.adb.is_app_running(
                app=self, max_retries=1, wait_time=1
            ):
                self.update_world_state(
                    new_app_state=AppState.CLOSED,
                    new_game_state=GameState.NOT_STARTED,
                    new_battle_sub_state=BattleState.IDLE,
                )
                self.curr_screen = None
                self.logger.info("Revomon app closed successfully.")
                return True
        except ConnectionError:
            # Connection error during check - assume closed since close_app succeeded
            self.logger.debug(
                "ADB connection error during verification, assuming closed"
            )
            self.update_world_state(
                new_app_state=AppState.CLOSED,
                new_game_state=GameState.NOT_STARTED,
                new_battle_sub_state=BattleState.IDLE,
            )
            self.curr_screen = None
            self.logger.info("Revomon app closed successfully.")
            return True

        self.logger.warning("App may still be running after close attempt.")
        return False
