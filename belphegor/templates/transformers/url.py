import discord
from discord import app_commands as ac
from yarl import URL

from belphegor import errors

#=============================================================================================================================#

class URLTransformer(ac.Transformer):
    def __init__(self, schemes = ["http", "https"]):
        self.schemes = schemes
        self._accept_string = "/".join(schemes)

    async def transform(self, interaction: discord.Interaction, value: str) -> URL:
        value = value.lstrip("<").rstrip(">")
        url = URL(value)
        if url.scheme in self.schemes:
            if url.scheme and url.host and url.path:
                return url
            else:
                raise errors.InvalidInput("Malformed URL.")
        else:
            raise errors.InvalidInput(f"This command accepts url with scheme {self._accept_string} only.")
