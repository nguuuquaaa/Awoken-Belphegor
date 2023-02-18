import discord
from discord import ui
from discord.utils import MISSING
from typing import TypeVar

from . import views, items

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.StandardView, covariant = True)

class Select(items.Item[_V], ui.Select[_V]):
    __custom_ui_init_fields__ = ["custom_id", "placeholder", "min_values", "max_values", "options", "row", "disabled"]

    custom_id: str = MISSING
    placeholder: str = None
    min_values: int = 1
    max_values: int = 1
    options: list[discord.SelectOption] = MISSING
    row: int = None
    disabled: bool = False
