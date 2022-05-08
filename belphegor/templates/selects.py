import discord
from discord import ui
from discord.utils import MISSING
from collections.abc import AsyncGenerator
from typing_extensions import Self
import asyncio

from belphegor.ext_types import Select
from belphegor.utils import copy_signature
from .metas import BaseItem

#=============================================================================================================================#

@copy_signature(Select)
class BaseSelect(BaseItem, Select):
    pass
