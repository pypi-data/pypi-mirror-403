import time
from logging import getLogger

logger = getLogger(__name__)


class Action(dict):
    def __init__(
        self,
        action_id: int | None = None,
        status: bool | None = None,
        error_message: str | None = None,
        action_name: str | None = None,
        state_diff: dict = {},
        last_action: dict = {},
    ):
        super().__init__()
        # Initialize with default values
        self.update(
            {
                "action_id": action_id,
                "status": status,
                "error_message": error_message,
                "action_name": action_name,
                "state_diff": state_diff,
                "last_action": last_action,
            }
        )

    def __setitem__(self, key, value):
        allowed_keys = {
            "action_id",
            "status",
            "error_message",
            "action_name",
            "state_diff",
            "last_action",
        }
        if key not in allowed_keys:
            raise KeyError(f"Invalid key: {key}. Only {allowed_keys} are allowed")
        super().__setitem__(key, value)

    def update(self, other=None, **kwargs):
        if other is not None:
            for k, v in other.items() if hasattr(other, "items") else other:
                self[k] = v
        for k, v in kwargs.items():
            self[k] = v

    def __delitem__(self, key):
        raise TypeError("Deleting keys is not allowed")


class Actions(list):
    def __init__(self, *args, **kwargs):
        super().__init__()
        if args and isinstance(args[0], (list, tuple)):
            for item in args[0]:
                self.append(item)

    def append(self, item):
        if not isinstance(item, Action):
            raise TypeError("Only FixedKeysDict objects can be added to this list")
        super().append(item)

    def extend(self, items):
        for item in items:
            self.append(item)

    def __setitem__(self, index, value):
        if not isinstance(value, Action):
            raise TypeError("Only FixedKeysDict objects can be added to this list")
        super().__setitem__(index, value)

    def __delitem__(self, index):
        raise TypeError("Removing items is not allowed")

    def remove(self, value):
        raise TypeError("Removing items is not allowed")

    def pop(self, index=-1):
        raise TypeError("Removing items is not allowed")

    def clear(self):
        raise TypeError("Clearing the list is not allowed")


def action(func):
    def wrapper(self, *args, **kwargs):
        # Dynamic resolution of components
        revomon = getattr(self, "revomon", self)
        bluestacks = getattr(
            self, "bluestacks", getattr(self, "pymordial_controller", None)
        )
        if bluestacks and hasattr(bluestacks, "bluestacks"):
            bluestacks = bluestacks.bluestacks

        # Use provided logger or fall back to module logger
        inst_logger = getattr(self, "logger", logger)

        def get_state_value(value):
            # Convert enum values to their string representation
            if hasattr(value, "name"):
                return value.name
            return str(value) if value is not None else None

        def get_current_state_dict():
            state = {
                "current_screen": get_state_value(
                    getattr(revomon, "curr_screen", None)
                ),
                "tv_current_page": get_state_value(
                    getattr(revomon, "tv_current_page", None)
                ),
                "tv_slot_selected": get_state_value(
                    getattr(revomon, "tv_slot_selected", None)
                ),
                "tv_searching_for": get_state_value(
                    getattr(revomon, "tv_searching_for", None)
                ),
                "current_city": get_state_value(getattr(revomon, "current_city", None)),
                "current_location": get_state_value(
                    getattr(revomon, "current_location", None)
                ),
                "game_state": get_state_value(getattr(revomon, "game_state", None)),
                "battle_sub_state": get_state_value(
                    getattr(revomon, "battle_sub_state", None)
                ),
            }

            # Add Bluestacks state if available
            if bluestacks:
                b_state = None
                if hasattr(bluestacks, "state"):
                    b_state = bluestacks.state.current_state
                elif hasattr(bluestacks, "bluestacks_state"):
                    b_state = bluestacks.bluestacks_state.current_state
                state["bluestacks_state"] = get_state_value(b_state)

            # Add App state if available
            if hasattr(revomon, "app_state"):
                state["app_state"] = get_state_value(revomon.app_state.current_state)

            return state

        def wait_for_action(action: str, timeout: int = 60) -> bool:
            """Action verification using the registry pattern."""
            inst_logger.info(
                f"Waiting for '{action}' action to complete (timeout: {timeout}s)..."
            )
            try:
                # Resolve action_registry from self or revomon
                registry = getattr(
                    self, "action_registry", getattr(revomon, "action_registry", None)
                )

                if not registry:
                    inst_logger.error(
                        f"Action {action} failed: 'action_registry' not found."
                    )
                    return False

                handler = registry.get_handler(action)
                # Pass self (controller OR app) to wait_for_completion
                success = handler.wait_for_completion(self, timeout)
                if success:
                    inst_logger.info(f"Action '{action}' completed successfully")
                else:
                    inst_logger.warning(f"Action '{action}' timed out")
                return success
            except KeyError:
                inst_logger.error(f"No handler registered for action '{action}'")
                raise
            except Exception as e:
                inst_logger.error(f"Error in action handler for '{action}': {e}")
                raise

        old_state = get_current_state_dict()
        current_action = Action()
        success = False
        error_msg = None
        MAX_RETRIES = 3

        # Retry Loop
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Execute the action logic (clicks, swipes, etc.)
                func(self, *args, **kwargs)

                # Wait for action to complete using the OOP handler system
                action_success = wait_for_action(action=func.__name__)

                # Check if action completed successfully
                if action_success:
                    success = True
                    break
                else:
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            f"Action {func.__name__} timed out (Attempt {attempt}/{MAX_RETRIES}). Retrying..."
                        )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in {func.__name__} (Attempt {attempt}): {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(1)

        new_state = get_current_state_dict()

        # Build the Action record
        current_action.update(
            {
                "action_id": len(revomon.actions) + 1,
                "status": success,
                "error_message": error_msg if not success else None,
                "action_name": func.__name__,
                "state_diff": {
                    k: {"prev": str(old_state.get(k)), "new": str(new_state.get(k))}
                    for k in set(old_state) | set(new_state)
                    if old_state.get(k) != new_state.get(k)
                },
                "last_action": (
                    {
                        "action_id": (
                            revomon.last_action["action_id"]
                            if revomon.last_action and revomon.last_action["action_id"]
                            else None
                        ),
                        "status": (
                            revomon.last_action["status"]
                            if revomon.last_action and revomon.last_action["status"]
                            else None
                        ),
                        "action_name": (
                            revomon.last_action["action_name"]
                            if revomon.last_action
                            and revomon.last_action["action_name"]
                            else None
                        ),
                    }
                    if revomon.last_action
                    else None
                ),
            }
        )

        # Append Action to Actions
        revomon.actions.append(current_action)
        revomon.last_action = current_action

        if not success:
            inst_logger.error(
                f"Action {func.__name__} failed permanently after 3 attempts."
            )

        return revomon.last_action

    return wrapper
