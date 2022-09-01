import discord
import re
import contextlib
from collections.abc import Iterable
from typing import TYPE_CHECKING

from belphegor import utils

#=============================================================================================================================#

if TYPE_CHECKING:
    from belphegor.bot import Interaction

#=============================================================================================================================#

class ProgressBar:
    def __init__(self, *, progress_message: str = "Working...", done_message: str = "Done.", length: int = 20):
        self.progress_message = progress_message
        self.done_message = done_message
        self.length = length

    def construct(self, rate: float):
        rate = max(min(rate, 1.0), 0.0)
        bf = "\u2588" * int(rate * self.length)
        c = "\u2591"
        return f"{bf:{c}<{self.length}} {rate * 100:.2f}%"

    def progress(self, rate: float):
        return f"{self.progress_message}\nProgress: {self.construct(rate)}"

    def done(self):
        return f"{self.done_message}\nProgress: {self.construct(1.0)}"

class InteractionHelper:
    @staticmethod
    async def response(interaction: "Interaction", /, content: str = None, **kwargs):
        """|coro|
        Send or edit response message, depends on whether it was already sent or not.
        Aside from the first argument being the interaction that is reponded to, the other arguments are the same as InteractionResponse.send_message

        Parameters
        -----------
        content: Optional[:class:`str`]
            The content of the message to send.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        view: :class:`discord.ui.View`
            The view to send with the message.
        ephemeral: :class:`bool`
            Indicates if the message should only be visible to the user who started the interaction.
            If a view is sent with an ephemeral message and it has no timeout set then the timeout
            is set to 15 minutes.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. See :meth:`.abc.Messageable.send` for
            more information.
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This sends the message without any embeds if set to ``True``.

        Raises
        -------
        HTTPException
            Sending the message failed.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``.
        ValueError
            The length of ``embeds`` was invalid.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if interaction.message is None:
            await interaction.response.send_message(content, **kwargs)
        else:
            await interaction.response.edit_message(content = content, **kwargs)

    @staticmethod
    async def followup(interaction: "Interaction", content: str = None, **kwargs):
        """|coro|
        Send or edit followup message, depends on whether it was already sent or not.
        Aside from the first argument being the interaction that is reponded to, the other arguments are the same as Webhook.send

        Parameters
        ------------
        content: :class:`str`
            The content of the message to send.
        wait: :class:`bool`
            Whether the server should wait before sending a response. This essentially
            means that the return type of this function changes from ``None`` to
            a :class:`WebhookMessage` if set to ``True``. If the type of webhook
            is :attr:`WebhookType.application` then this is always set to ``True``.
        username: :class:`str`
            The username to send with this message. If no username is provided
            then the default username for the webhook is used.
        avatar_url: :class:`str`
            The avatar URL to send with this message. If no avatar URL is provided
            then the default avatar for the webhook is used. If this is not a
            string then it is explicitly cast using ``str``.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        ephemeral: :class:`bool`
            Indicates if the message should only be visible to the user.
            This is only available to :attr:`WebhookType.application` webhooks.
            If a view is sent with an ephemeral message and it has no timeout set
            then the timeout is set to 15 minutes.

            .. versionadded:: 2.0
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.

            .. versionadded:: 1.4
        view: :class:`discord.ui.View`
            The view to send with the message. You can only send a view
            if this webhook is not partial and has state attached. A
            webhook has state attached if the webhook is managed by the
            library.

            .. versionadded:: 2.0
        thread: :class:`~discord.abc.Snowflake`
            The thread to send this webhook to.

            .. versionadded:: 2.0
        thread_name: :class:`str`
            The thread name to create with this webhook if the webhook belongs
            to a :class:`~discord.ForumChannel`. Note that this is mutually
            exclusive with the ``thread`` parameter, as this will create a
            new thread with the given name.

            .. versionadded:: 2.0
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This sends the message without any embeds if set to ``True``.

            .. versionadded:: 2.0

        Raises
        --------
        HTTPException
            Sending the message failed.
        NotFound
            This webhook was not found.
        Forbidden
            The authorization token for the webhook is incorrect.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``
            or ``thread`` and ``thread_name``.
        ValueError
            The length of ``embeds`` was invalid, there was no token
            associated with this webhook or ``ephemeral`` was passed
            with the improper webhook type or there was no state
            attached with this webhook when giving it a view.

        Returns
        ---------
        Optional[:class:`WebhookMessage`]
            If ``wait`` is ``True`` then the message that was sent, otherwise ``None``.
        """
        if interaction.message is None:
            await interaction.followup.send(content, **kwargs)
        else:
            await interaction.message.edit(content = content, **kwargs)

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