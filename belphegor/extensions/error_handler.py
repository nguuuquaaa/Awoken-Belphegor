import discord
from discord.ext import commands
import traceback
import sys
import asyncio

from belphegor import utils
from belphegor.settings import settings
from belphegor.bot import Belphegor
from belphegor.templates.discord_types import Interaction, File

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class ErrorHandler(commands.Cog):
    error_hook: discord.Webhook

    def __init__(self, bot: Belphegor):
        self.bot = bot

    async def get_error_hook(self):
        await self.bot.wait_until_ready()
        ch = self.bot.get_channel(settings.LOG_CHANNEL_ID)
        self.error_hook = (await ch.webhooks())[0]

    async def cog_load(self):
        self.old_on_error = self.bot.on_error
        self.old_app_command_error = self.bot.tree.on_error

        self.bot.on_error = self.on_error
        self.bot.tree.on_error = self.on_app_command_error

        asyncio.create_task(self.get_error_hook())

    def cog_unload(self):
        self.bot.on_error = self.old_on_error
        self.bot.tree.on_error = self.old_app_command_error

    async def send_error_hook(self, msg: str):
        now = utils.now()
        await self.error_hook.send(file = File.from_str(msg, now.strftime("%Y-%m-%d %H-%M-%S") + ".log"))

    async def on_error(self, event, *args, **kwargs):
        etype, e, etb = sys.exc_info()
        if not isinstance(e, discord.Forbidden):
            prt_err = "".join(traceback.format_exception(e))
            msg = f"Event {event} raised an error:\n{prt_err}"
            log.error(msg)
            await self.send_error_hook(msg)

    async def on_app_command_error(self, interaction: Interaction, error: Exception):
        if not isinstance(error, discord.Forbidden):
            prt_err = "\n".join(traceback.format_exception(error))
            msg = f"Interaction {interaction.type.name} raised an error:\n{prt_err}"
            log.error(msg)
            await self.send_error_hook(msg)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
