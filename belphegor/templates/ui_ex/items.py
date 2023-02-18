from discord import ui
import typing

#=============================================================================================================================#

from .metas import BaseItem

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = ui.View, covariant = True)

class Item(BaseItem, ui.Item[_V]):
    pass