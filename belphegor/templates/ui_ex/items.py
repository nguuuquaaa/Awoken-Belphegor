from discord import ui
import typing
from typing_extensions import TypeVar
from collections.abc import Callable, Awaitable

from . import discord_types, views
from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.View, default = views.View)

class Item(BaseItem, ui.Item[_V]):
    def __call__(self, func: Callable[[discord_types.Interaction], Awaitable]):
        self.callback = func
