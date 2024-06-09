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

class Blueprint:
    "A blueprint contains all static elements of a to-be-sended message."

    content: typing.Any = MISSING
    embed: discord.Embed = MISSING
    embeds: Sequence[discord.Embed] = MISSING
    file: discord.File = MISSING
    files: Sequence[discord.File] = MISSING
    tts: bool = False
    ephemeral: bool = False
    allowed_mentions: discord.AllowedMentions = MISSING

    def __init__(self,
        content: typing.Any = MISSING,
        *,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        self.content = content
        self.embed = embed
        self.embeds = embeds
        self.file = file
        self.files = files
        self.tts = tts
        self.ephemeral = ephemeral
        self.allowed_mentions = allowed_mentions

    def merge(self, blueprint: "Blueprint"):
        """Update self with non-missing attributes of the target blueprint."""

        self.tts = blueprint.tts
        self.ephemeral = blueprint.ephemeral
        for key in ("content", "embed", "embeds", "file", "files", "allowed_mentions"):
            value = getattr(blueprint, key)
            if value is not MISSING:
                setattr(self, key, value)

        return self

    def update(
        self,
        *,
        content: typing.Any = MISSING,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        tts: bool = MISSING,
        ephemeral: bool = MISSING,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        """Update multiple attributes."""

        for key, value in (
            ("content", content),
            ("embed", embed),
            ("embeds", embeds),
            ("file", file),
            ("files", files),
            ("tts", tts),
            ("ephemeral", ephemeral),
            ("allowed_mentions", allowed_mentions)
        ):
            if value is None:
                setattr(self, key, MISSING)
            elif value is not MISSING:
                setattr(self, key, value)

        return self

#=============================================================================================================================#

class ControlPanel:
    """A control panel is a representation of the "reaction chain" that a slash command sends and listens to, but specifically contained in a single message."""

    target_message: discord.Message = None

    @property
    def blueprint(self) -> Blueprint:
        return self._blueprint

    @blueprint.setter
    def blueprint(self, value: Blueprint):
        self._blueprint = value

    @property
    def view(self) -> ui_ex.View | None:
        return self._view

    @view.setter
    def view(self, value: ui_ex.View | None):
        if value is not None:
            value.panel = self
        self._view = value

    def __new__(cls, *args, **kwargs) -> typing.Self:
        obj = super().__new__(cls)
        obj.target_message = None
        obj.blueprint = Blueprint()
        obj.view = None
        return obj

    def __init__(self):
        pass

    def edit_blueprint(
        self,
        *,
        content: typing.Any = MISSING,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        tts: bool = MISSING,
        ephemeral: bool = MISSING,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        self.blueprint.update(
            content = content,
            embed = embed,
            embeds = embeds,
            file = file,
            files = files,
            tts = tts,
            ephemeral = ephemeral,
            allowed_mentions = allowed_mentions
        )
        return self

    @classmethod
    def from_parts(
        cls,
        *,
        content: typing.Any = MISSING,
        embed: discord.Embed = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        file: discord.File = MISSING,
        files: Sequence[discord.File] = MISSING,
        tts: bool = MISSING,
        ephemeral: bool = MISSING,
        allowed_mentions: discord.AllowedMentions = MISSING
    ):
        obj = cls()
        obj.edit_blueprint(
            content = content,
            embed = embed,
            embeds = embeds,
            file = file,
            files = files,
            tts = tts,
            ephemeral = ephemeral,
            allowed_mentions = allowed_mentions
        )
        return obj

    async def reply(self, interaction: Interaction):
        """Reply to an interaction."""

        blueprint = self.blueprint
        view = self.view
        match interaction.response.is_done(), self.target_message:
            case True, None:
                self.target_message = await interaction.followup.send(
                    blueprint.content,
                    embed = blueprint.embed,
                    embeds = blueprint.embeds,
                    file = blueprint.file,
                    files = blueprint.files,
                    tts = blueprint.tts,
                    ephemeral = blueprint.ephemeral,
                    allowed_mentions = blueprint.allowed_mentions,
                    view = view or MISSING,
                    wait = True
                )

            case True, msg:
                await msg.edit(
                    content = blueprint.content or None,
                    embeds = blueprint.embeds if blueprint.embeds else [blueprint.embed] if blueprint.embed else [],
                    attachments = blueprint.files if blueprint.files else [blueprint.file] if blueprint.file else [],
                    allowed_mentions = blueprint.allowed_mentions or None,
                    view = view
                )

            case False, None:
                await interaction.response.send_message(
                    blueprint.content,
                    embed = blueprint.embed,
                    embeds = blueprint.embeds,
                    file = blueprint.file,
                    files = blueprint.files,
                    tts = blueprint.tts,
                    ephemeral = blueprint.ephemeral,
                    allowed_mentions = blueprint.allowed_mentions,
                    view = view or MISSING
                )
                self.target_message = await interaction.original_response()

            case False, _:
                await interaction.response.edit_message(
                    content = blueprint.content or None,
                    embeds = blueprint.embeds if blueprint.embeds else [blueprint.embed] if blueprint.embed else [],
                    attachments = blueprint.files if blueprint.files else [blueprint.file] if blueprint.file else [],
                    allowed_mentions = blueprint.allowed_mentions or None,
                    view = view
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

    async def defer(self, interaction: Interaction, *, ephemeral: bool = MISSING):
        if ephemeral is MISSING:
            ephemeral = self.blueprint.ephemeral
        else:
            self.blueprint.ephemeral = ephemeral

        if interaction.response.is_done():
            pass
        else:
            await interaction.response.defer(ephemeral = ephemeral)

    def stop(self):
        "Stop listening."
        if self.view:
            self.view.stop()
