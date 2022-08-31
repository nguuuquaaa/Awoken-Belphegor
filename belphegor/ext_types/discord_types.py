import discord
from discord import ui
import io
from typing import Awaitable, TypeVar, TYPE_CHECKING
from typing_extensions import Self
from collections.abc import Callable

from belphegor.bot import Interaction

#=============================================================================================================================#

class File(discord.File):
    @classmethod
    def from_str(cls, s: str, filename: str = "text.txt", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(s.encode("utf-8")), filename, spoiler = spoiler, description = description)

    @classmethod
    def from_bytes(cls, b: bytes | bytearray, filename: str = "file", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(b), filename, spoiler = spoiler, description = description)
