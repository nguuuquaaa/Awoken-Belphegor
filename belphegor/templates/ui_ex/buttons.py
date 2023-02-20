import discord
from discord import ui
import typing
import abc

from belphegor import utils
from . import views, items, modals
from ..discord_types import Interaction

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = views.StandardView)

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

    @abc.abstractmethod
    async def callback(self, interaction: Interaction):
        pass

class InputButton(Button[_V]):
    label: str = "Input"
    emoji: EmojiType = "\U0001f4dd"
    style: discord.ButtonStyle = discord.ButtonStyle.primary

    input_modal: modals.InputModal

    def create_modal(self) -> modals.InputModal:
        modal = utils.get_default_attribute(self, "input_modal")
        return modal

    async def callback(self, interaction: Interaction):
        modal = self.create_modal()
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

    input_modal: modals.JumpToModal

    def create_modal(self) -> modals.JumpToModal:
        return super().create_modal()

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
