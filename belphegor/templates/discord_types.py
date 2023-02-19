import discord
import io
import typing

#=============================================================================================================================#

if typing.TYPE_CHECKING:
    from belphegor.bot import Belphegor

#=============================================================================================================================#

class File(discord.File):
    @classmethod
    def from_str(cls, s: str, filename: str = "text.txt", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(s.encode("utf-8")), filename, spoiler = spoiler, description = description)

    @classmethod
    def from_bytes(cls, b: bytes | bytearray, filename: str = "file", *, spoiler: bool = False, description: str | None = None):
        return discord.File(io.BytesIO(b), filename, spoiler = spoiler, description = description)

class Interaction(discord.Interaction):
    @property
    def client(self) -> "Belphegor":
        """:class:`Belphegor`: The client that is handling this interaction."""
        return self._client