import logging
from typing import TYPE_CHECKING

from pymordialblue.bluestacks_controller import PymordialBluestacksController

from .models.app import RevomonApp
from .models.mixins import (
    BagLogicMixin,
    BattleLogicMixin,
    CoreLifecycleMixin,
    MenuLogicMixin,
    NavigationLogicMixin,
    TVLogicMixin,
)
from .models.navigator import Navigator

if TYPE_CHECKING:
    from .models.app import RevomonApp


class RevomonController(
    PymordialBluestacksController,
    CoreLifecycleMixin,
    NavigationLogicMixin,
    MenuLogicMixin,
    BattleLogicMixin,
    TVLogicMixin,
    BagLogicMixin,
):
    """
    Main controller for Revomon automation.
    Inherits capability from Pymordial (Device Control) and Logic Mixins (Game Actions).
    Holds a reference to the RevomonApp instance for shared state access.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.revomon = RevomonApp()
        self.navigator = Navigator(self)
        self.logger = logging.getLogger(__name__)
