from logging import Logger, getLogger
from typing import TYPE_CHECKING

from pymordial import PymordialScreen

from ..elements import tv_advanced_search_elements

if TYPE_CHECKING:
    from pymordial import PymordialController


class TvAdvancedSearchScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="tv_advanced_search",
            elements={
                "tv_advanced_search_button": tv_advanced_search_elements.tv_advanced_search_button,
            },
        )
        self.logger: Logger = getLogger(__name__)
