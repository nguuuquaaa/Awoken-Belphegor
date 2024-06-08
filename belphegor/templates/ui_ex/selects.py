import discord
from discord import ui
from discord.utils import MISSING
from typing_extensions import TypeVar
import abc

from . import views, items
from ..discord_types import Interaction

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.View, default = views.View)

class Select(items.Item[_V], ui.Select[_V]):
    __custom_ui_init_fields__ = ["custom_id", "placeholder", "min_values", "max_values", "options", "row", "disabled"]

    custom_id: str = MISSING
    placeholder: str = None
    min_values: int = 1
    max_values: int = 1
    options: list[discord.SelectOption] = MISSING
    row: int = None
    disabled: bool = False

    @abc.abstractmethod
    async def callback(self, interaction: Interaction):
        pass

class SelectOne(Select[_V]):
    placeholder: str = "Select"
    min_values: int = 1
    max_values: int = 1
