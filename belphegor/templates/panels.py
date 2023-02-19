import discord
from discord.utils import MISSING
import typing
from collections.abc import Sequence

from belphegor import utils
from . import ui_ex
from .discord_types import Interaction

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class Panel:
    """A panel is a self-contained pair of message and view that listens and responses to itself."""

    target_message: discord.Message = None
    content: typing.Any = MISSING
    embed: discord.Embed = MISSING
    embeds: Sequence[discord.Embed] = MISSING
    file: discord.File = MISSING
    files: Sequence[discord.File] = MISSING
    tts: bool = False
    ephemeral: bool = False
    allowed_mentions: discord.AllowedMentions = MISSING

    @property
    def view(self) -> ui_ex.StandardView:
        return self._view

    @view.setter
    def view(self, value: ui_ex.StandardView):
        if value:
            value.panel = self
        self._view = value

    def __init__(self,
        content: typing.Any = MISSING,
        *,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        view: ui_ex.StandardView = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        self.target_message = None
        self.content = content
        self.embed = embed
        self.embeds = embeds
        self.file = file
        self.files = files
        self.view = view
        self.tts = tts
        self.ephemeral = ephemeral
        self.allowed_mentions = allowed_mentions

    async def reply(self, interaction: Interaction):
        """
        Reply to an interaction.
        """
        match interaction.response.is_done(), self.target_message:
            case True, None:
                self.target_message = await interaction.followup.send(
                    self.content,
                    embed = self.embed,
                    embeds = self.embeds,
                    file = self.file,
                    files = self.files,
                    view = self.view,
                    tts = self.tts,
                    ephemeral = self.ephemeral,
                    allowed_mentions = self.allowed_mentions,
                    wait = True
                )

            case True, _:
                msg = self.target_message = interaction.message
                await msg.edit(
                    content = self.content or None,
                    embeds = self.embeds if self.embeds else [self.embed] if self.embed else [],
                    attachments = self.files if self.files else [self.file] if self.file else [],
                    view = self.view,
                    allowed_mentions = self.allowed_mentions or None
                )

            case False, None:
                await interaction.response.send_message(
                    self.content,
                    embed = self.embed,
                    embeds = self.embeds,
                    file = self.file,
                    files = self.files,
                    view = self.view,
                    tts = self.tts,
                    ephemeral = self.ephemeral,
                    allowed_mentions = self.allowed_mentions
                )
                self.target_message = await interaction.original_response()

            case False, _:
                await interaction.response.edit_message(
                    content = self.content or None,
                    embeds = self.embeds if self.embeds else [self.embed] if self.embed else [],
                    attachments = self.files if self.files else [self.file] if self.file else [],
                    view = self.view,
                    allowed_mentions = self.allowed_mentions or None
                )

    async def thinking(self, interaction: Interaction):
        """
        Reply with "Bot is thinking..."
        """
        thinking_msg = f"<a:typing:1014969925787455558> {interaction.client.user.display_name} is thinking..."

        match interaction.response.is_done(), self.target_message:
            case True, None:
                self.target_message = await interaction.followup.send(thinking_msg, wait = True)

            case True, msg:
                await msg.edit(content = thinking_msg, embeds = [], attachments = [])

            case False, None:
                await interaction.response.defer(thinking = True)

            case False, _:
                await interaction.response.edit_message(content = thinking_msg, embeds = [], attachments = [])

    async def defer(self, interaction: Interaction):
        if interaction.response.is_done():
            pass
        else:
            await interaction.response.defer(ephemeral = self.ephemeral)
