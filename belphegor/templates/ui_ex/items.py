from discord import ui
import typing

from. import views
from .metas import BaseItem

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = views.StandardView, covariant = True)

class Item(BaseItem, ui.Item[_V]):
    pass
