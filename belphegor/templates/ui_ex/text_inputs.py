import discord
from discord import ui
from typing import TypeVar

from . import views
from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.StandardView, covariant = True)

class TextInput(BaseItem, ui.TextInput[_V]):
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
