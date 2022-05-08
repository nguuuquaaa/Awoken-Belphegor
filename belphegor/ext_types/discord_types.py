import discord
from discord import ui
import io
from typing import Awaitable
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

class _AddCallbackMixin:
    def add_callback(self, callback: Callable[[Interaction], Awaitable]):
        self.callback = callback

class View(_AddCallbackMixin, ui.View):
    async def on_timeout(self) -> None:
        self.stop()

class Modal(_AddCallbackMixin, ui.Modal):
    async def on_timeout(self) -> None:
        self.stop()

class Button(_AddCallbackMixin, ui.Button[View]):
    pass

class Select(_AddCallbackMixin, ui.Select[View]):
    pass

class TextInput(_AddCallbackMixin, ui.TextInput[View]):
    pass
