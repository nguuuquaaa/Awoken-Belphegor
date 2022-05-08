import discord
from discord import ui
import io
from typing import Awaitable, TypeVar
from typing_extensions import Self
from collections.abc import Callable

from belphegor.bot import Belphegor

#=============================================================================================================================#

class File(discord.File):
    @classmethod
    def from_str(cls, s: str, filename: str = "text.txt", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(s.encode("utf-8")), filename, spoiler = spoiler, description = description)

    @classmethod
    def from_bytes(cls, b: bytes | bytearray, filename: str = "file", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(b), filename, spoiler = spoiler, description = description)

#=============================================================================================================================#

class Interaction(discord.Interaction):
    @property
    def client(self) -> Belphegor:
        """:class:`Client`: The client that is handling this interaction."""
        return self._client

class View(ui.View):
    async def on_timeout(self) -> None:
        self.stop()

class Modal(ui.Modal):
    async def on_timeout(self) -> None:
        self.stop()

_V = TypeVar("_V", bound = View, covariant = True)

class Item(ui.Item[_V]):
    pass

class Button(ui.Button[_V]):
    pass

class Select(ui.Select[_V]):
    pass

class TextInput(ui.TextInput[_V]):
    pass
