import discord
from discord import ui
import asyncio
from collections.abc import AsyncGenerator
from typing import TypeVar, ForwardRef
from typing_extensions import Self

from belphegor.ext_types import Interaction
from belphegor.utils import copy_signature
from .buttons import InputButton as OrigInputButton, ExitButton

#=============================================================================================================================#

class StandardView(ui.View):
    allowed_user: discord.User
    already_sent: bool

    def __init__(self, *, timeout: int | float = 180.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout)
        self.allowed_user = allowed_user
        self.already_sent = False

    def add_exit_button(self, row: int = 0) -> Self:
        self.add_item(ExitButton(row = row))
        return self

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.allowed_user is None:
            return True
        else:
            return interaction.user == self.allowed_user

    async def response_to(self, interaction: Interaction, **kwargs):
        kwargs.pop("view", None)
        if self.already_sent:
            await interaction.response.edit_message(view = self, **kwargs)
        else:
            await interaction.response.send_message(view = self, **kwargs)
            self.already_sent = True

#=============================================================================================================================#

_CV = TypeVar("_CV", bound = ForwardRef("ContinuousInputView"))

class ContinuousInputView(StandardView):
    input_button: "InputButton"

    class InputButton(OrigInputButton[_CV]):
        pass

    def __init__(self, *, timeout: int | float = 180.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout, allowed_user = allowed_user)
        self.input_button = self.InputButton()
        self.add_item(self.input_button)
        self.add_exit_button()

    async def setup(self, interaction: Interaction) -> AsyncGenerator[tuple[Interaction, ui.TextInput]]:
        modal = self.input_button.create_modal()
        asyncio.create_task(interaction.response.send_modal(modal))
        async for interaction, input in self.input_button.wait_for_inputs():
            yield interaction, input
