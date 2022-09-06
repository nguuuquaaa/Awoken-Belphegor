import discord
from discord import ui
from discord.utils import MISSING
import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any

from .typing_utils import copy_signature
from .log_utils import get_logger

#=============================================================================================================================#

if TYPE_CHECKING:
    from belphegor.ext_types import Interaction, File

log = get_logger()

#=============================================================================================================================#

class ResponseHelper:
    interaction: "Interaction"
    target_message: discord.Message

    def __init__(self, interaction: "Interaction"):
        self.interaction = interaction
        self.target_message = None

    async def send(
        self,
        content: Any = None,
        *,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        view: ui.View = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        """
        Send a response.
        Action type (new/edit) depends on whether a message has been send as an interaction response or not.
        """
        if self.interaction.response.is_done():
            if self.target_message is None:
                if self.interaction.message is None:
                    self.target_message = await self.interaction.followup.send(
                        content,
                        embed = embed,
                        embeds = embeds,
                        file = file,
                        files = files,
                        view = view,
                        tts = tts,
                        ephemeral = ephemeral,
                        allowed_mentions = allowed_mentions,
                        wait = True
                    )
                else:
                    self.target_message = self.interaction.message
                    await self.target_message.edit(
                        content = content or None,
                        embeds = embeds if embeds else [embed] if embed else [],
                        attachments = files if files else [file] if file else [],
                        view = view,
                        allowed_mentions = allowed_mentions or None
                    )
            else:
                await self.target_message.edit(
                        content = content or None,
                        embeds = embeds if embeds else [embed] if embed else [],
                        attachments = files if files else [file] if file else [],
                        view = view,
                        allowed_mentions = allowed_mentions or None
                    )
        else:
            if self.interaction.message is None:
                await self.interaction.response.send_message(
                        content,
                        embed = embed,
                        embeds = embeds,
                        file = file,
                        files = files,
                        view = view,
                        tts = tts,
                        ephemeral = ephemeral,
                        allowed_mentions = allowed_mentions
                    )
                self.target_message = await self.interaction.original_response()
            else:
                await self.interaction.response.edit_message(
                        content = content or None,
                        embeds = embeds if embeds else [embed] if embed else [],
                        attachments = files if files else [file] if file else [],
                        view = view,
                        allowed_mentions = allowed_mentions or None
                    )

        target_messages = getattr(view, "target_messages", None)
        if target_messages is not None:
            target_messages.add(self.target_message)

    async def thinking(self):
        """
        Response with "Bot is thinking..."
        Action type (new/edit) depends on whether a message has been send as an interaction response or not.
        """
        thinking_msg = f"<a:typing:1014969925787455558> {self.interaction.client.user.display_name} is thinking..."
        if self.interaction.response.is_done():
            if self.target_message is None:
                if self.interaction.message is None:
                    self.target_message = await self.interaction.followup.send(thinking_msg, wait = True)
                else:
                    self.target_message = self.interaction.message
                    await self.target_message.edit(content = thinking_msg, embeds = [], attachments = [])
            else:
                await self.target_message.edit(content = thinking_msg, embeds = [], attachments = [])
        else:
            if self.interaction.message is None:
                await self.interaction.response.defer(thinking = True)
            else:
                await self.interaction.response.edit_message(content = thinking_msg, embeds = [], attachments = [])

class QueryHelper:
    @staticmethod
    def broad_search(name: str, fields: Iterable[str]) -> list[dict]:
        return [
            {
                field: {
                    "$regex": ".*?".join(map(re.escape, name.split())),
                    "$options": "i"
                }
            } for field in fields
        ]