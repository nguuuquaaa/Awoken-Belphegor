
class InteractionHelper:
    @staticmethod
    async def response_to(interaction, /, content: str = None, **kwargs):
        """
        Send or edit response message, depends on whether it was sent or not.
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