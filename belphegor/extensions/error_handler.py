import discord
from discord.ext import commands
import sys
import traceback
from PIL import Image
import aiohttp

from belphegor import utils
from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class ErrorHandler(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot
        bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: Interaction, exception: Exception):
        t = "\n".join(traceback.format_exception(exception))
        log.error(f"{type(exception)}: {exception}\n{t}")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
