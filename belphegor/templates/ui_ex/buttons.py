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

class BlueButton(Button[_V]):
    style: discord.ButtonStyle = discord.ButtonStyle.primary

class GrayButton(Button[_V]):
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

class GreenButton(Button[_V]):
    style: discord.ButtonStyle = discord.ButtonStyle.success

class RedButton(Button[_V]):
    style: discord.ButtonStyle = discord.ButtonStyle.danger

class URLButton(Button[_V]):
    style: discord.ButtonStyle = discord.ButtonStyle.link

#=============================================================================================================================#

class InputButton(BlueButton[_V]):
    label: str = "Input"
    emoji: EmojiType = "\U0001f4dd"

    input_modal: modals.InputModal

    def create_modal(self) -> modals.InputModal:
        modal = utils.get_default_attribute(self, "input_modal")
        return modal

    async def callback(self, interaction: Interaction):
        modal = self.create_modal()
        await interaction.response.send_modal(modal)

class HomeButton(BlueButton[_V]):
    label: str = "Home"
    emoji: EmojiType = "\U0001f3e0"

class ExitButton(GrayButton[_V]):
    label: str = "Exit"
    emoji: EmojiType = "\u274c"

    async def callback(self, interaction: Interaction):
        self.view.stop()
        for item in self.view.children:
            item.disabled = True

        await interaction.response.edit_message(view = self.view)

class ConfirmedButton(GrayButton[_V]):
    label: str = None
    emoji: EmojiType = "\u2705"

class DeniedButton(GrayButton[_V]):
    label: str = None
    emoji: EmojiType = "\u2716"

#=============================================================================================================================#

class NextButton(GrayButton[_V]):
    label: str = None
    emoji: EmojiType = "\u25b6"

class PreviousButton(GrayButton[_V]):
    label: str = None
    emoji: EmojiType = "\u25c0"

class JumpForwardButton(GrayButton[_V]):
    jump: int = 5
    label: str = "Forward 5"
    emoji: EmojiType = "\u23e9"

class JumpBackwardButton(GrayButton[_V]):
    jump: int = 5
    label: str = "Back 5"
    emoji: EmojiType = "\u23ea"

class JumpToButton(InputButton[_V]):
    label: str = "Jump to"
    emoji: EmojiType = "\u23fa"
    style: discord.ButtonStyle = discord.ButtonStyle.secondary

    input_modal: modals.JumpToModal

    def create_modal(self) -> modals.JumpToModal:
        return super().create_modal()

#=============================================================================================================================#

class StatsButton(BlueButton[_V]):
    label: str = "Stats"
    emoji: EmojiType = None

class TriviaButton(BlueButton[_V]):
    label: str = "Trivia"
    emoji: EmojiType = "\U0001f5d2"

class SkinsButton(BlueButton[_V]):
    label: str = "Skins"
    emoji: EmojiType = "\U0001f5bc"
