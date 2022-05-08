import discord
from discord import app_commands as ac, ui, enums
from discord.ext import commands
import importlib
import sys
import traceback
import textwrap
import asyncio
from io import StringIO
from contextlib import redirect_stdout

from belphegor.bot import Belphegor
from belphegor.ext_types.discord_types import Interaction
from belphegor.templates.views import ContinuousInputView
from belphegor.templates.checks import Check
from belphegor import utils

#=============================================================================================================================#

class Admin(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @ac.command(name = "reload")
    @ac.describe(extension = "Extension to reload")
    @ac.check(Check.owner_only())
    async def reload(
        self,
        interaction: Interaction,
        extension: str
    ):
        fullname_extension = f"belphegor.cogs.{extension}"
        try:
            if fullname_extension in self.bot.extensions:
                await self.bot.reload_extension(fullname_extension)
            else:
                await self.bot.load_extension(fullname_extension)
        except commands.ExtensionError:
            await interaction.response.send_message(f"```\nFailed reloading {extension}:\n{traceback.format_exc()}```")
        else:
            await self.bot.tree.sync()
            print(f"Reloaded {fullname_extension}")
            await interaction.response.send_message(f"```\nSuccess reloading {extension}```")

    @ac.command(name = "reimport")
    @ac.describe(module = "Module to reimport")
    @ac.check(Check.owner_only())
    async def reimport(
        self,
        interaction: Interaction,
        module: str
    ):
        m = importlib.import_module(f"belphegor.{module}")
        try:
            importlib.reload(m)
        except:
            traceback.print_exc()
            await interaction.response.send_message(f"```\Failed reimporting {module}```")
        else:
            print(f"Reimported belphegor.{module}")
            await interaction.response.send_message(f"```\nSuccess reimporting {module}```")

    @ac.command(name = "eval")
    @ac.check(Check.owner_only())
    async def _eval(
        self,
        interaction: Interaction
    ):
        view = ContinuousInputView(allowed_user = interaction.user)
        async for interaction, input in view.setup(interaction):
            code = f"async def func():\n{textwrap.indent(input.value, '    ')}"
            env = {
                "bot": self.bot,
                "interaction": interaction,
                "discord": discord,
                "commands": commands,
                "utils": utils,
                "asyncio": asyncio
            }
            try:
                exec(code, env)
            except Exception as e:
                embed = discord.Embed()
                embed.add_field(name = "Input", value = f"```py\n{input.value}\n```", inline = False)
                embed.add_field(name = "Output", value = f"```py\n{e}\n```", inline = False)
                await interaction.response.edit_message(embed = embed)
            stdout = StringIO()
            func = env["func"]
            try:
                with redirect_stdout(stdout):
                    await func()
            except:
                add_text = f"\n{traceback.format_exc()}"
            else:
                add_text = "\n"
            finally:
                value = stdout.getvalue()
                if value or add_text:
                    ret = (value + add_text).strip()
                    embed = discord.Embed()
                    embed.add_field(name = "Input", value = f"```py\n{input.value}\n```", inline = False)
                    if len(ret) > 1950:
                        await interaction.response.edit_message(embed = embed, attachments = [discord.File.from_str(ret, "output.txt")])
                    elif len(ret) > 0:
                        embed.add_field(name = "Output", value = f"```\n{ret}\n```", inline = False)
                        await interaction.response.edit_message(embed = embed)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Admin(bot))