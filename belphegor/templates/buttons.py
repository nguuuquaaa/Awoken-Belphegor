import discord
from discord import ui
from discord.enums import ButtonStyle
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing_extensions import Self
import asyncio
from functools import cached_property

from belphegor.ext_types import Interaction, Button, View, Modal, TextInput
from belphegor.utils import copy_signature
from .metas import BaseItem

#=============================================================================================================================#

@copy_signature(Button)
class BaseButton(BaseItem, Button):
    pass

@copy_signature(BaseButton)
class InputButton(BaseButton):
    label = "Input"
    emoji = "\U0001f4dd"
    style = ButtonStyle.primary
    queue: asyncio.Queue[tuple[Interaction, TextInput]]

    class InputModal(Modal, title = "Input"):
        view: View
        queue: asyncio.Queue[tuple[Interaction, TextInput]]

        input = TextInput(
            label = "Input",
            style = discord.TextStyle.long
        )

        async def on_submit(self, interaction: Interaction):
            await self.queue.put((interaction, self.input))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = asyncio.Queue()

    def create_modal(self, *, title: str = MISSING, custom_id: str = MISSING):
        modal = self.InputModal(title = title, timeout = self.view.timeout, custom_id = custom_id)
        modal.queue = self.queue
        modal.view = self.view
        return modal

    async def callback(self, interaction: Interaction):
        modal = self.create_modal()
        await interaction.response.send_modal(modal)

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, TextInput]]:
        while not self.disabled:
            try:
                interaction, text_input = await asyncio.wait_for(self.queue.get(), timeout = self.view.timeout)
            except asyncio.TimeoutError:
                return
            else:
                yield interaction, text_input

class HomeButton(BaseButton):
    label = "Home"
    emoji = "\U0001f3e0"
    style = ButtonStyle.primary

class ExitButton(BaseButton):
    label = "Exit"
    emoji = "\u274c"
    style = ButtonStyle.secondary

    async def callback(self, interaction: Interaction):
        view = self.view
        for component in view.children:
            component.disabled = True
        view.stop()

        await interaction.response.edit_message(view = view)

class ConfirmedButton(BaseButton):
    label = None
    emoji = "\u2705"
    style = ButtonStyle.secondary

class DeniedButton(BaseButton):
    label = None
    emoji = "\u2716"
    style = ButtonStyle.secondary

#=============================================================================================================================#

class NextButton(BaseButton):
    label = None
    emoji = "\u25b6"
    style = ButtonStyle.secondary

class PreviousButton(BaseButton):
    label = None
    emoji = "\u25c0"
    style = ButtonStyle.secondary

class JumpForwardButton(BaseButton):
    jump = 5
    label = f"Forward {jump}"
    emoji = "\u23e9"
    style = ButtonStyle.secondary

class JumpBackwardButton(BaseButton):
    jump = 5
    label = f"Back {jump}"
    emoji = "\u23ea"
    style = ButtonStyle.secondary

class JumpToButton(InputButton):
    label = "Jump to"
    emoji = "\u23fa"
    style = ButtonStyle.secondary
    queue: asyncio.Queue[tuple[Interaction, "InputModal.IntTextInput"]]

    class InputModal(InputButton.InputModal):
        queue: asyncio.Queue[tuple[Interaction, "IntTextInput"]]

        class IntTextInput(TextInput):
            @cached_property
            def int_value(self):
                return int(self.value)

        input = IntTextInput(
            label = "Jump to page",
            style = discord.TextStyle.short
        )

    async def wait_for_inputs(self) -> AsyncGenerator[tuple[Interaction, InputModal.IntTextInput]]:
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

class TriviaButton(BaseButton):
    label = "Trivia"
    emoji = "\U0001f5d2"
    style = ButtonStyle.primary

class SkinsButton(BaseButton):
    label = "Skins"
    emoji = "\U0001f5bc"
    style = ButtonStyle.primary
