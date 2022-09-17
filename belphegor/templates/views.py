import discord
from discord import ui
import asyncio
from collections.abc import AsyncGenerator
from typing import TypeVar, ForwardRef
from typing_extensions import Self

from belphegor import utils
from belphegor.ext_types import Interaction
from .buttons import InputButton as OrigInputButton, ExitButton
from .metas import MetaMergeClasstypeProperty

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class StandardView(ui.View):
    allowed_user: discord.User
    target_messages: set[discord.Message]

    def __init__(self, *, timeout: int | float = 180.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout)
        self.allowed_user = allowed_user
        self.target_messages = set()

    def add_exit_button(self, row: int = 0) -> Self:
        self.add_item(ExitButton(row = row))
        return self

    async def interaction_check(self, interaction: Interaction) -> bool:
        if self.allowed_user is None:
            return True
        else:
            return interaction.user == self.allowed_user

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        for message in self.target_messages:
            await message.edit(view = self)

#=============================================================================================================================#

_CV = TypeVar("_CV", bound = ForwardRef("ContinuousInputView"))

class ContinuousInputView(StandardView, metaclass = MetaMergeClasstypeProperty):
    input_button: "InputButton"

    class InputButton(OrigInputButton[_CV]):
        pass

    def __init__(self, *, timeout: int | float = 180.0, allowed_user: discord.User = None):
        super().__init__(timeout = timeout, allowed_user = allowed_user)
        self.input_button = self.InputButton(label = "Input")
        self.add_item(self.input_button)
        self.add_exit_button()

    async def setup(self, interaction: Interaction) -> AsyncGenerator[tuple[Interaction, InputButton.InputModal.ModalTextInput]]:
        modal = self.input_button.create_modal()
        asyncio.create_task(interaction.response.send_modal(modal))
        async for interaction, input in self.input_button.wait_for_inputs():
            yield interaction, input
