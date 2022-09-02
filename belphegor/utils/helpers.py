import discord
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

from .typing_utils import copy_signature
from .log_utils import get_logger

#=============================================================================================================================#

if TYPE_CHECKING:
    from belphegor.ext_types import Interaction

log = get_logger()

#=============================================================================================================================#

class ResponseHelper:
    interaction: "Interaction"
    target_message: discord.Message

    def __init__(self, interaction: "Interaction"):
        self.interaction = interaction
        self.target_message = None

    @copy_signature(discord.InteractionResponse.send_message)
    async def send(self, content: str = None, **kwargs):
        if self.interaction.response.is_done():
            if self.target_message is None:
                if self.interaction.message is None:
                    kwargs.pop("wait", None)
                    self.target_message = await self.interaction.followup.send(content, wait = True, **kwargs)
                else:
                    self.target_message = self.interaction.message
                    await self.target_message.edit(content = content, **kwargs)
            else:
                await self.target_message.edit(content = content, **kwargs)
        else:
            if self.interaction.message is None:
                await self.interaction.response.send_message(content, **kwargs)
                self.target_message = await self.interaction.original_response()
            else:
                await self.interaction.response.edit_message(content = content, **kwargs)

    async def thinking(self):
        """
        Response with "Bot is thinking..."
        """
        thinking_msg = f"<a:typing:1014969925787455558> {self.interaction.client.user.display_name} is thinking..."
        if self.interaction.response.is_done():
            if self.target_message is None:
                if self.interaction.message is None:
                    self.target_message = await self.interaction.followup.send(thinking_msg, wait = True)
                else:
                    self.target_message = self.interaction.message
                    await self.target_message.edit(content = thinking_msg, embed = None)
            else:
                await self.target_message.edit(content = thinking_msg, embed = None)
        else:
            if self.interaction.message is None:
                await self.interaction.response.defer(thinking = True)
            else:
                await self.interaction.response.edit_message(content = thinking_msg, embed = None)

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