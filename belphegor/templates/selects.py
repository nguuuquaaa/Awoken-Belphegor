import discord
from discord import ui
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing import TypeVar
import asyncio

from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = ui.View)

class BaseSelect(BaseItem, ui.Select[_V]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
