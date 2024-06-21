import discord
from discord import app_commands as ac
from discord.ext import commands
import traceback
import sys
import asyncio
import contextlib

from belphegor import utils, errors
from belphegor.settings import settings
from belphegor.bot import Belphegor
from belphegor.templates.discord_types import Interaction, File
from belphegor.templates.panels import ControlPanel

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class ErrorHandler(commands.Cog):
    _error_hook: discord.Webhook

    def __init__(self, bot: Belphegor):
        self.bot = bot
        self._wait_done = asyncio.Event()

    async def _fetch_error_hook(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(settings.LOG_CHANNEL_ID)
        hooks = await channel.webhooks()
        self._error_hook = hooks[0]
        self._wait_done.set()

    @contextlib.asynccontextmanager
    async def error_hook(self):
        await self._wait_done.wait()
        yield self._error_hook

    async def cog_load(self):
        self.old_on_error = self.bot.on_error
        self.old_app_command_error = self.bot.tree.on_error

        self.bot.on_error = self.on_error
        self.bot.tree.on_error = self.on_app_command_error

        asyncio.create_task(self._fetch_error_hook())

    def cog_unload(self):
        self.bot.on_error = self.old_on_error
        self.bot.tree.on_error = self.old_app_command_error

    async def send_error(self, msg: str):
        now = utils.now()
        async with self.error_hook() as hook:
            await hook.send(file = File.from_str(msg, now.strftime("%Y-%m-%d %H-%M-%S") + ".log"))

    async def on_error(self, event, *args, **kwargs):
        etype, e, etb = sys.exc_info()
        if not isinstance(e, discord.Forbidden):
            prt_err = "".join(traceback.format_exception(e))
            msg = f"Event {event} raised an error:\n{prt_err}"
            log.error(msg)
            await self.send_error(msg)

    async def on_app_command_error(self, interaction: Interaction, error: Exception):
        if not isinstance(error, discord.Forbidden):
            if isinstance(error, errors.CustomError):
                await ControlPanel.from_parts(content = error.message).reply(interaction)
            elif isinstance(error, ac.TransformerError):
                cause = error.__cause__
                if isinstance(cause, errors.CustomError):
                    await ControlPanel.from_parts(content = cause.message).reply(interaction)
                else:
                    await ControlPanel.from_parts(content = f"Unrecognized value:\n```\n{error.value}\n```").reply(interaction)
            else:
                prt_err = "\n".join(traceback.format_exception(error))
                msg = f"Interaction {interaction.type.name} raised an error:\n{prt_err}"
                log.error(msg)
                await self.send_error(msg)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
