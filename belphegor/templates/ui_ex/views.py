import discord
from discord import ui
import typing

from .metas import PostInitable
from ..discord_types import Interaction

if typing.TYPE_CHECKING:
    from ..panels import ControlPanel

#=============================================================================================================================#

class View(PostInitable, ui.View):
    panel: "ControlPanel"
    allowed_user: discord.User

    def __init__(self, *, timeout: int | float = 300.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout)
        self.allowed_user = allowed_user
        self.target_messages = set()

    def add_exit_button(self, row: int = 0):
        from . import buttons
        self.add_item(buttons.ExitButton(row = row))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.allowed_user is None:
            return True
        else:
            return interaction.user == self.allowed_user

    def shutdown(self):
        self.stop()
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        self.shutdown()
        if self.panel.target_message:
            await self.panel.target_message.edit(view = self)
