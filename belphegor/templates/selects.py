import discord
from discord import ui
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing import TypeVar
import asyncio

from belphegor.ext_types import Select, View
from belphegor.utils import copy_signature
from .metas import BaseItem

#=============================================================================================================================#

_V = TypeVar("_V", bound = View)

class BaseSelect(BaseItem, Select[_V]):
    @copy_signature(Select.__init__)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
