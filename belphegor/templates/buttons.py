import discord
from discord import ui, utils
from discord.enums import ButtonStyle
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing import TypeVar, TypeAlias, TYPE_CHECKING
import asyncio
from functools import cached_property
from pydantic import Field

from belphegor import utils
from belphegor.ext_types import Interaction
from .metas import BaseItem, MetaMergeClasstypeProperty
from .text_inputs import TextInput
from .modals import Modal

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

_V = TypeVar("_V", bound = ui.View, covariant = True)

EmojiType: TypeAlias = str | discord.Emoji | discord.PartialEmoji

class BaseButton(BaseItem, ui.Button[_V]):
    __custom_ui_init_fields__ = ["custom_id", "label", "emoji", "style", "url", "row", "disabled"]

    custom_id: str = None
    label: str = None
    emoji: EmojiType = None
    style: ButtonStyle = ButtonStyle.secondary
    url: str = None
    row: int = None
    disabled: bool = False

class InputButton(BaseButton[_V]):
    label: str = "Input"
    emoji: EmojiType = "\U0001f4dd"
    style: ButtonStyle = ButtonStyle.primary
    queue: asyncio.Queue[tuple[Interaction, TextInput[_V]]] = Field(init = False)

    class InputModal(Modal, metaclass = MetaMergeClasstypeProperty):
        title: str = "Input"
        queue: asyncio.Queue[tuple[Interaction, TextInput[_V]]]
        input: "ModalTextInput[_V]"

        class ModalTextInput(TextInput[_V]):
            label: str = "Input"
            style: discord.TextStyle = discord.TextStyle.long

        def __post_init__(self):
            self.input = self.ModalTextInput()
            self.add_item(self.input)

        async def on_submit(self, interaction: Interaction):
            await self.queue.put((interaction, self.input))

    def __post_init__(self):
        self.queue = asyncio.Queue()

    def create_modal(self, *, title: str = MISSING, custom_id: str = MISSING) -> InputModal:
        modal = self.InputModal(title = title, timeout = self.view.timeout, custom_id = custom_id)
        modal.queue = self.queue
        return modal

    async def callback(self, interaction: Interaction):
        modal = self.create_modal()
        await interaction.response.send_modal(modal)

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, "InputModal.ModalTextInput[_V]"]]:
        while not self.disabled:
            done, pending = await asyncio.wait([self.queue.get(), self.view.wait()], return_when = asyncio.FIRST_COMPLETED)
            ret = tuple(done)[0].result()
            if isinstance(ret, bool):
                asyncio.create_task(self.queue.put(None))
                return
            else:
                yield ret

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
    label: str = "Forward 5"
    emoji: EmojiType = "\u23e9"
    style: ButtonStyle = ButtonStyle.secondary

class JumpBackwardButton(BaseButton[_V]):
    jump: int = 5
    label: str = "Back 5"
    emoji: EmojiType = "\u23ea"
    style: ButtonStyle = ButtonStyle.secondary

class JumpToButton(InputButton[_V]):
    label: str = "Jump to"
    emoji: EmojiType = "\u23fa"
    style: ButtonStyle = ButtonStyle.secondary
    queue: asyncio.Queue[tuple[Interaction, "InputModal.TextInput[_V]"]] = Field(init = False)

    class InputModal(Modal):
        label = "Jump"

        class ModalTextInput(TextInput):
            label = "Jump to page"
            style = discord.TextStyle.short

            @cached_property
            def int_value(self):
                return int(self.value)

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, "InputModal.ModalTextInput[_V]"]]:
        while not self.disabled:
            done, pending = await asyncio.wait([self.queue.get(), self.view.wait()], return_when = asyncio.FIRST_COMPLETED)
            ret = tuple(done)[0].result()
            if isinstance(ret, bool):
                asyncio.create_task(self.queue.put(None))
                return
            else:
                interaction, text_input = ret
                try:
                    text_input.int_value
                except ValueError:
                    asyncio.create_task(interaction.response.edit_message())
                else:
                    yield interaction, text_input

#=============================================================================================================================#

class StatsButton(BaseButton[_V]):
    label: str = "Stats"
    emoji: EmojiType = None
    style: ButtonStyle = ButtonStyle.primary

class TriviaButton(BaseButton[_V]):
    label: str = "Trivia"
    emoji: EmojiType = "\U0001f5d2"
    style: ButtonStyle = ButtonStyle.primary

class SkinsButton(BaseButton[_V]):
    label: str = "Skins"
    emoji: EmojiType = "\U0001f5bc"
    style: ButtonStyle = ButtonStyle.primary
