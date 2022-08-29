import discord
from discord.ui import Button, View, Modal, TextInput
from discord.enums import ButtonStyle
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing import TypeVar, TypeAlias
from typing_extensions import Self
import asyncio
from functools import cached_property
from pydantic import Field, BaseModel

from belphegor.ext_types import Interaction
from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = View, covariant = True)

EmojiType: TypeAlias = str | discord.Emoji | discord.PartialEmoji

class BaseButton(BaseItem, Button[_V]):
    label: str = None
    emoji: EmojiType = None
    style: ButtonStyle = ButtonStyle.secondary
    url: str = None
    row: int = None
    custom_id: str = None
    disabled: bool = False

class InputButton(BaseButton[_V]):
    label: str = "Input"
    emoji: EmojiType = "\U0001f4dd"
    style: ButtonStyle = ButtonStyle.primary
    queue: asyncio.Queue[tuple[Interaction, TextInput[_V]]] = Field(init = False)

    class InputModal(Modal, title = "Input"):
        view: _V
        queue: asyncio.Queue[tuple[Interaction, TextInput[_V]]]

        input = TextInput[_V](
            label = "Input",
            style = discord.TextStyle.long
        )

        async def on_submit(self, interaction: Interaction):
            await self.queue.put((interaction, self.input))

    def __post_init__(self):
        self.queue = asyncio.Queue()

    def create_modal(self, *, title: str = MISSING, custom_id: str = MISSING) -> InputModal:
        modal = self.InputModal(title = title, timeout = self.view.timeout, custom_id = custom_id)
        modal.queue = self.queue
        modal.view = self.view
        return modal

    async def callback(self, interaction: Interaction):
        modal = self.create_modal()
        await interaction.response.send_modal(modal)

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, TextInput[_V]]]:
        while not self.disabled:
            try:
                interaction, text_input = await asyncio.wait_for(self.queue.get(), timeout = self.view.timeout)
            except asyncio.TimeoutError:
                return
            else:
                yield interaction, text_input

class HomeButton(BaseButton[_V]):
    label: str = "Home"
    emoji: EmojiType = "\U0001f3e0"
    style: ButtonStyle = ButtonStyle.primary

class ExitButton(BaseButton[_V]):
    label: str = "Exit"
    emoji: EmojiType = "\u274c"
    style: ButtonStyle = ButtonStyle.secondary

    async def callback(self, interaction: Interaction):
        view = self.view
        for component in view.children:
            component.disabled = True
        view.stop()

        await interaction.response.edit_message(view = view)

class ConfirmedButton(BaseButton[_V]):
    label: str = None
    emoji: EmojiType = "\u2705"
    style: ButtonStyle = ButtonStyle.secondary

class DeniedButton(BaseButton[_V]):
    label: str = None
    emoji: EmojiType = "\u2716"
    style: ButtonStyle = ButtonStyle.secondary

#=============================================================================================================================#

class NextButton(BaseButton[_V]):
    label: str = None
    emoji: EmojiType = "\u25b6"
    style: ButtonStyle = ButtonStyle.secondary

class PreviousButton(BaseButton[_V]):
    label: str = None
    emoji: EmojiType = "\u25c0"
    style: ButtonStyle = ButtonStyle.secondary

class JumpForwardButton(BaseButton[_V]):
    jump: int = 5
    label: str = f"Forward {jump}"
    emoji: EmojiType = "\u23e9"
    style: ButtonStyle = ButtonStyle.secondary

class JumpBackwardButton(BaseButton[_V]):
    jump: int = 5
    label: str = f"Back {jump}"
    emoji: EmojiType = "\u23ea"
    style: ButtonStyle = ButtonStyle.secondary

class JumpToButton(InputButton[_V]):
    label: str = "Jump to"
    emoji: EmojiType = "\u23fa"
    style: ButtonStyle = ButtonStyle.secondary
    queue: asyncio.Queue[tuple[Interaction, "InputModal.IntTextInput[_V]"]] = Field(init = False)

    class InputModal(InputButton.InputModal):
        queue: asyncio.Queue[tuple[Interaction, "IntTextInput[_V]"]]

        class IntTextInput(TextInput[_V]):
            @cached_property
            def int_value(self):
                return int(self.value)

        input = IntTextInput[_V](
            label = "Jump to page",
            style = discord.TextStyle.short
        )

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, InputModal.IntTextInput[_V]]]:
        while not self.disabled:
            try:
                interaction, text_input = await asyncio.wait_for(self.queue.get(), timeout = self.view.timeout)
            except asyncio.TimeoutError:
                return
            else:
                try:
                    text_input.int_value
                except ValueError:
                    asyncio.create_task(interaction.response.edit_message(content = "Hey, the input value isn't even an integer.", view = self.view))
                else:
                    yield interaction, text_input

#=============================================================================================================================#

class TriviaButton(BaseButton[_V]):
    label: str = "Trivia"
    emoji: EmojiType = "\U0001f5d2"
    style: ButtonStyle = ButtonStyle.primary

class SkinsButton(BaseButton[_V]):
    label: str = "Skins"
    emoji: EmojiType = "\U0001f5bc"
    style: ButtonStyle = ButtonStyle.primary
