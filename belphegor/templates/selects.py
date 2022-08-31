import discord
from discord.ui import Select, View
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing import TypeVar
import asyncio

from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = View)

class BaseSelect(BaseItem, Select[_V]):
    __custom_ui_init_fields__ = ["custom_id", "placeholder", "min_values", "max_values", "options", "row", "disabled"]

    custom_id: str = MISSING
    placeholder: str = None
    min_values: int = 1
    max_values: int = 1
    options: list[discord.SelectOption] = MISSING
    row: int = None
    disabled: bool = False
