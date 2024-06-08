import discord
from discord import ui
from typing_extensions import TypeVar
from functools import cached_property

from . import views, items

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.View, default = views.View)

class TextInput(items.Item[_V], ui.TextInput[_V]):
    __custom_ui_init_fields__ = ["custom_id", "label", "style", "placeholder", "default", "required", "min_length", "max_length", "row"]

    custom_id: str = None
    label: str = None
    style: discord.TextStyle = discord.TextStyle.short
    placeholder: str = None
    default: str = None
    required: bool = True
    min_length: int = None
    max_length: int = None
    row: int = None

class InputTextBox(TextInput):
    label: str = "Input"
    style: discord.TextStyle = discord.TextStyle.long

class JumpToTextBox(TextInput):
    label: str = "Jump to page"
    style: discord.TextStyle = discord.TextStyle.short

    @cached_property
    def int_value(self) -> int:
        return int(self.value)
