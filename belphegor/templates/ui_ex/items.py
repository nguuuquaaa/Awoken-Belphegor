from discord import ui
from typing_extensions import TypeVar

from . import views
from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = views.View, default = views.View)

class Item(BaseItem, ui.Item[_V]):
    pass
