import discord
from discord import app_commands as ac
from discord.ext import commands

from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction
from belphegor.templates.checks import Check

#=============================================================================================================================#

class Help(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @ac.command(name = "belhelp")
    async def belhelp(
        self,
        interaction: Interaction
    ):
        pass

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Help(bot))
