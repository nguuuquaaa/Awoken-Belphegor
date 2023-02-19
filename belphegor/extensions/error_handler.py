import discord
from discord.ext import commands
import traceback
import sys

from belphegor import utils
from belphegor.settings import settings
from belphegor.bot import Belphegor
from belphegor.templates.discord_types import Interaction

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class ErrorHandler(commands.Cog):
    error_hook: discord.Webhook

    def __init__(self, bot: Belphegor):
        self.bot = bot

    async def cog_load(self):
        self.old_on_error = self.bot.on_error
        self.old_app_command_error = self.bot.tree.on_error

        self.bot.on_error = self.on_error
        self.bot.tree.on_error = self.on_app_command_error

        ch = self.bot.get_channel(settings.LOG_CHANNEL_ID)
        self.error_hook = (await ch.webhooks())[0]

    def cog_unload(self):
        self.bot.on_error = self.old_on_error
        self.bot.tree.on_error = self.old_app_command_error

    async def on_error(self, event, *args, **kwargs):
        etype, e, etb = sys.exc_info()
        if not isinstance(e, discord.Forbidden):
            prt_err = "".join(traceback.format_exception(e))
            msg = f"```\nIgnoring exception in event {event}:\n{prt_err}\n```"
            log.info(msg)
            await self.error_hook.execute(msg)

    async def on_app_command_error(self, interaction: Interaction, exception: Exception):
        if not isinstance(exception, discord.Forbidden):
            prt_err = "\n".join(traceback.format_exception(exception))
            msg = f"```\nIgnoring exception in interaction {interaction.type.name}:\n{prt_err}\n```"
            log.info(msg)
            await self.error_hook.execute(msg)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
