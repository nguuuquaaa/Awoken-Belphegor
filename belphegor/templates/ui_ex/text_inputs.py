import discord
from discord import ui
import typing

from . import views, items

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = views.StandardView, covariant = True)

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
