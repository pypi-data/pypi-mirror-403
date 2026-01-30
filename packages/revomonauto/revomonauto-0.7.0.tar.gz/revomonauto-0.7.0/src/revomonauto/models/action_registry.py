"""
Action Registry for RevomonApp.

This module provides a centralized registry for mapping action names to their
corresponding verification handlers.

Design Pattern: Registry Pattern with type-safe lookups

Usage:
    # Initialize registry
    registry = ActionRegistry()

    # Register handlers
    registry.register("open_main_menu", ScreenTransitionHandler(["main_menu"]))

    # Get handler at runtime
    handler = registry.get_handler("open_main_menu")
    success = handler.wait_for_completion(app, timeout=60)
"""

from logging import getLogger
from typing import Dict

from .action_handlers import ActionHandler

logger = getLogger(__name__)


class ActionRegistry:
    """
    Central registry mapping action names to verification handlers.

    This class follows the Registry pattern to decouple action execution
    from action verification logic.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, ActionHandler] = {}
        logger.debug("ActionRegistry initialized")

    def register(self, action_name: str, handler: ActionHandler) -> None:
        """
        Register a handler for a specific action.

        Args:
            action_name: The name of the action (must match @action method name)
            handler: The ActionHandler instance to handle verification

        Raises:
            ValueError: If action_name is invalid
            TypeError: If handler is not an ActionHandler instance
        """
        if not action_name or not isinstance(action_name, str):
            raise ValueError(f"Invalid action_name: {action_name}")

        if not isinstance(handler, ActionHandler):
            raise TypeError(
                f"Handler must be an ActionHandler instance, got {type(handler)}"
            )

        if action_name in self._handlers:
            logger.warning(f"Overwriting existing handler for action '{action_name}'")

        self._handlers[action_name] = handler
        logger.debug(
            f"Registered handler {handler.__class__.__name__} for action '{action_name}'"
        )

    def get_handler(self, action_name: str) -> ActionHandler:
        """
        Retrieve the handler for a specific action.

        Args:
            action_name: The name of the action

        Returns:
            The registered ActionHandler instance

        Raises:
            KeyError: If no handler is registered for this action
        """
        if action_name not in self._handlers:
            available = ", ".join(sorted(self._handlers.keys()))
            raise KeyError(
                f"No handler registered for action '{action_name}'. "
                f"Available actions: {available}"
            )

        return self._handlers[action_name]

    def is_registered(self, action_name: str) -> bool:
        """
        Check if a handler is registered for an action.

        Args:
            action_name: The name of the action to check

        Returns:
            True if handler exists, False otherwise
        """
        return action_name in self._handlers

    def get_all_actions(self) -> list[str]:
        """
        Get a list of all registered action names.

        Returns:
            Sorted list of action names
        """
        return sorted(self._handlers.keys())

    def unregister(self, action_name: str) -> None:
        """
        Remove a handler from the registry.

        Args:
            action_name: The name of the action to unregister

        Raises:
            KeyError: If no handler is registered for this action
        """
        if action_name not in self._handlers:
            raise KeyError(f"No handler registered for action '{action_name}'")

        del self._handlers[action_name]
        logger.debug(f"Unregistered handler for action '{action_name}'")

    def clear(self) -> None:
        """Remove all handlers from the registry."""
        count = len(self._handlers)
        self._handlers.clear()
        logger.info(f"Cleared {count} handlers from registry")

    def __len__(self) -> int:
        """Return the number of registered handlers."""
        return len(self._handlers)

    def __contains__(self, action_name: str) -> bool:
        """Support 'in' operator: 'action_name' in registry"""
        return action_name in self._handlers

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ActionRegistry({len(self._handlers)} actions registered)"
