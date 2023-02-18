import discord
from discord import ui
import typing
from functools import cached_property
import abc

from belphegor.ext_types import Interaction
from . import views, items, text_inputs, modals

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = views.StandardView, covariant = True)

EmojiType: typing.TypeAlias = str | discord.Emoji | discord.PartialEmoji

class Button(items.Item[_V], ui.Button[_V]):
    __custom_ui_init_fields__ = ["custom_id", "label", "emoji", "style", "url", "row", "disabled"]

    custom_id: str = None
    label: str = None
    emoji: EmojiType = None
    style: discord.ButtonStyle = discord.ButtonStyle.secondary
    url: str = None
    row: int = None
    disabled: bool = False

class InputButton(Button[_V]):
    label: str = "Input"
    emoji: EmojiType = "\U0001f4dd"
    style: discord.ButtonStyle = discord.ButtonStyle.primary

    class InputModal(modals.Modal):
        title: str = "Input"
        input_text_box: "InputTextBox"

        class InputTextBox(text_inputs.TextInput[_V]):
            label: str = "Input"
            style: discord.TextStyle = discord.TextStyle.long

        def __post_init__(self):
            self.input_text_box = self.InputTextBox()
            self.add_item(self.input_text_box)

        @abc.abstractmethod
        async def on_submit(self, interaction: Interaction):
            pass

    async def callback(self, interaction: Interaction):
        modal = self.InputModal(timeout = self.view.timeout)
        await interaction.response.send_modal(modal)

class HomeButton(Button[_V]):
    label: str = "Home"
    emoji: EmojiType = "\U0001f3e0"
    style: discord.ButtonStyle = discord.ButtonStyle.primary

class ExitButton(Button[_V]):
    label: str = "Exit"
    emoji: EmojiType = "\u274c"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

    async def callback(self, interaction: Interaction):
        self.view.stop()
        for item in self.view.children:
            item.disabled = True
        self.view.stop()

        await interaction.response.edit_message(view = self.view)

class ConfirmedButton(Button[_V]):
    label: str = None
    emoji: EmojiType = "\u2705"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class DeniedButton(Button[_V]):
    label: str = None
    emoji: EmojiType = "\u2716"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

#=============================================================================================================================#

class NextButton(Button[_V]):
    label: str = None
    emoji: EmojiType = "\u25b6"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class PreviousButton(Button[_V]):
    label: str = None
    emoji: EmojiType = "\u25c0"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class JumpForwardButton(Button[_V]):
    jump: int = 5
    label: str = "Forward 5"
    emoji: EmojiType = "\u23e9"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class JumpBackwardButton(Button[_V]):
    jump: int = 5
    label: str = "Back 5"
    emoji: EmojiType = "\u23ea"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class JumpToButton(InputButton[_V]):
    label: str = "Jump to"
    emoji: EmojiType = "\u23fa"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

    class InputModal(InputButton.InputModal):
        label: str = "Jump"
        input_text_box: "InputTextBox"

        class InputTextBox(InputButton.InputModal.InputTextBox):
            label: str = "Jump to page"
            style: discord.TextStyle = discord.TextStyle.short

            @cached_property
            def int_value(self):
                return int(self.value)

        @abc.abstractmethod
        async def on_submit(self, interaction: Interaction):
            return self.input_text_box.int_value

#=============================================================================================================================#

class StatsButton(Button[_V]):
    label: str = "Stats"
    emoji: EmojiType = None
    style: discord.ButtonStyle = discord.ButtonStyle.primary

class TriviaButton(Button[_V]):
    label: str = "Trivia"
    emoji: EmojiType = "\U0001f5d2"
    style: discord.ButtonStyle = discord.ButtonStyle.primary

class SkinsButton(Button[_V]):
    label: str = "Skins"
    emoji: EmojiType = "\U0001f5bc"
    style: discord.ButtonStyle = discord.ButtonStyle.primary
