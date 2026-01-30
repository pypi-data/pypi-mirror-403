"""
Action Handler System for RevomonApp.

This module provides an OOP-based action verification framework.

Design Patterns:
    - Strategy Pattern: Different handlers implement ActionHandler interface
    - Template Method: Base class defines algorithm, subclasses customize steps

Usage:
    handler = ScreenTransitionHandler(
        expected_screens=["main_menu"],
        fallback_screens=["battle", "login"]
    )
    success = handler.wait_for_completion(app, timeout=60)
"""

import time
from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, Callable, List, Optional

if TYPE_CHECKING:
    from ..revomon_controller import RevomonController

logger = getLogger(__name__)


class ActionHandler(ABC):
    """
    Abstract base class for all action verification handlers.

    Each handler knows how to verify that a specific type of action
    has completed successfully.
    """

    @abstractmethod
    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """
        Waits for the action to complete with a timeout.

        Args:
            controller: The RevomonController instance
            timeout: Maximum time to wait in seconds

        Returns:
            True if action completed successfully, False if timeout
        """
        pass


class NoWaitHandler(ActionHandler):
    """
    Handler for actions that don't require visual verification.

    Examples: toggle_auto_run, move, execute_movement_script

    Usage:
        handler = NoWaitHandler()
    """

    def __init__(self, action_name: Optional[str] = None):
        self.action_name = action_name

    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """Returns immediately without verification."""
        if self.action_name:
            logger.info(
                f"Action '{self.action_name}' does not require visual confirmation."
            )
        return True


class StateUpdateHandler(ActionHandler):
    """
    Handler for actions that immediately update state without screen transitions.

    Examples: recall_revomon, enter_pvp_queue, exit_pvp_queue

    Usage:
        handler = StateUpdateHandler(
            state_updates={'is_pvp_queued': True},
            on_success=lambda app: logger.info("PvP queue entered")
        )
    """

    def __init__(
        self,
        state_updates: Optional[dict] = None,
        on_success: Optional[Callable] = None,
    ):
        """
        Args:
            state_updates: Dict of {attribute_name: value} to set on app
            on_success: Optional callback to execute on completion
        """
        self.state_updates = state_updates or {}
        self.on_success = on_success

    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """Updates state and returns immediately."""
        # Apply state updates
        for attr, value in self.state_updates.items():
            setattr(controller.revomon, attr, value)
            logger.debug(f"Updated app.{attr} = {value}")

        # Call success callback
        if self.on_success:
            self.on_success(controller.revomon)

        return True


class ScreenTransitionHandler(ActionHandler):
    """
    Handler for actions that wait for specific screen(s) to appear.

    This is the most common handler type, used for navigation actions.

    Examples: open_main_menu, close_main_menu, login, start_game

    Usage:
        handler = ScreenTransitionHandler(
            expected_screens=["main_menu"],
            fallback_screens=["battle", "login"],  # Also acceptable
            on_success=lambda app, ss: logger.info("Menu opened")
        )
    """

    def __init__(
        self,
        expected_screens: List[str],
        fallback_screens: Optional[List[str]] = None,
        on_success: Optional[Callable] = None,
    ):
        """
        Args:
            expected_screens: List of screen names to check (OR logic)
            fallback_screens: Additional acceptable screens (e.g., login after disconnect)
            on_success: Optional callback(app, screenshot) to run on success
        """
        self.expected_screens = expected_screens
        self.fallback_screens = fallback_screens or []
        self.on_success = on_success

    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """Polls for expected screen until timeout."""
        start_time = time.time()

        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                logger.warning(
                    f"Timed out waiting for screens: {self.expected_screens}"
                )
                return False

            # Check expected screens
            for screen_name in self.expected_screens:
                if self._check_screen(controller, screen_name):
                    logger.info(f"[OK] Expected screen '{screen_name}' detected")
                    if self.on_success:
                        self.on_success(controller.revomon)
                    return True

            # Check fallback screens
            for screen_name in self.fallback_screens:
                if self._check_screen(controller, screen_name):
                    logger.info(f"[OK] Fallback screen '{screen_name}' detected")
                    if self.on_success:
                        self.on_success(controller.revomon)
                    return True

            # Small delay before next check
            time.sleep(0.3)

    def _check_screen(self, controller: "RevomonController", screen_name: str) -> bool:
        """Maps screen name to appropriate is_*_screen method."""
        # Note: These methods are now on the Controller (Mixins)
        screen_checkers = {
            "start_game": controller.is_start_game_screen,
            "login": controller.is_login_screen,
            "overworld": controller.is_overworld_screen,
            "main_menu": controller.is_main_menu_screen,
            "pvp_queue": controller.is_pvp_queued,
            "wardrobe": controller.is_wardrobe_screen,
            "friends_list": controller.is_friends_list_screen,
            "settings": controller.is_settings_screen,
            "revodex": controller.is_revodex_screen,
            "market": controller.is_market_screen,
            "discussion": controller.is_discussion_screen,
            "clan": controller.is_clan_screen,
            "battle": controller.is_on_battle_screen,
            "attacks_menu": controller.is_attacks_menu_screen,
            "team_bag": controller.is_team_bag_screen,
            "tv": controller.is_tv_screen,
        }

        checker = screen_checkers.get(screen_name)
        if not checker:
            logger.error(f"Unknown screen name: {screen_name}")
            return False

        try:
            return checker()
        except Exception as e:
            logger.error(f"Error checking screen '{screen_name}': {e}")
            return False


class CompositeHandler(ActionHandler):
    """
    Handler that combines multiple verification strategies.

    Useful for complex actions with multiple validation steps.

    Usage:
        handler = CompositeHandler([
            StateUpdateHandler(state_updates={'is_mon_recalled': True}),
            ScreenTransitionHandler(expected_screens=["overworld"])
        ])
    """

    def __init__(self, handlers: List[ActionHandler]):
        """
        Args:
            handlers: List of handlers to execute in sequence
        """
        self.handlers = handlers

    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """Executes all handlers, returns True only if all succeed."""
        start_time = time.time()

        for i, handler in enumerate(self.handlers):
            remaining_timeout = max(1, timeout - int(time.time() - start_time))
            logger.debug(
                f"Executing handler {i+1}/{len(self.handlers)} with {remaining_timeout}s timeout"
            )

            if not handler.wait_for_completion(controller, remaining_timeout):
                logger.warning(f"Handler {i+1}/{len(self.handlers)} failed")
                return False

        return True


class CustomHandler(ActionHandler):
    """
    Handler that uses a custom verification function.

    Useful for one-off actions with unique logic.

    Usage:
        def check_func(timeout):
            # Custom logic here
            return True

        handler = CustomHandler(check_func)
    """

    def __init__(self, check_function: Callable[[int], bool]):
        """
        Args:
            check_function: Function(timeout) -> bool
        """
        self.check_function = check_function

    def wait_for_completion(
        self, controller: "RevomonController", timeout: int = 60
    ) -> bool:
        """Delegates to custom check function."""
        return self.check_function(timeout)
