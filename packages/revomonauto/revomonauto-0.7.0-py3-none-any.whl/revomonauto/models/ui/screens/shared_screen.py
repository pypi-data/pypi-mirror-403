from logging import Logger, getLogger

from pymordial import PymordialScreen

from ..elements import shared_elements


class SharedScreen(PymordialScreen):
    def __init__(self):
        super().__init__(
            name="shared",
            elements={
                "chat_button": shared_elements.ChatButton(),
                "battle_chat_button": shared_elements.BattleChatButton(),
                "general_chat_button": shared_elements.GeneralChatButton(),
                "chat_log_image": shared_elements.ChatLogImage(),
                "exit_menu_button": shared_elements.ExitMenuButton(),
                "exit_menu_pixel": shared_elements.ExitMenuPixel(),
            },
        )
        self.logger: Logger = getLogger(__name__)
