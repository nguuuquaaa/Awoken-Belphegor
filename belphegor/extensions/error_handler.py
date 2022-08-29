import discord
from discord.ext import commands
import sys
import traceback
from PIL import Image
import aiohttp

from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction

#=============================================================================================================================#

class ErrorHandler(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, interaction: Interaction, exception: Exception):
        self.bot.log.error(f"{type(exception)}: {exception}\n{traceback.format_exception(exception)}")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
