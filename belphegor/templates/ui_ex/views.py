import discord
from discord import ui
import typing
from typing_extensions import Self

from .metas import PostInitable
from ..discord_types import Interaction

if typing.TYPE_CHECKING:
    from ..panels import Panel

#=============================================================================================================================#

class StandardView(PostInitable, ui.View):
    panel: "Panel"
    allowed_user: discord.User

    def __init__(self, *, timeout: int | float = 180.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout)
        self.allowed_user = allowed_user
        self.target_messages = set()

    def add_exit_button(self, row: int = 0) -> Self:
        from . import buttons
        self.add_item(buttons.ExitButton(row = row))
        return self

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.allowed_user is None:
            return True
        else:
            return interaction.user == self.allowed_user

    async def on_timeout(self):
        self.stop()
        for item in self.children:
            item.disabled = True

        if self.panel.target_message:
            await self.panel.reply(view = self)
