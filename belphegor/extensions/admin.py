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
import os
import typing
import enum

from belphegor.bot import Belphegor
from belphegor.ext_types.discord_types import Interaction
from belphegor.templates.buttons import BaseButton, EmojiType
from belphegor.templates.views import ContinuousInputView, StandardView
from belphegor.templates.checks import Check
from belphegor import utils

#=============================================================================================================================#

log = utils.get_logger()
all_extensions = [fn[:-3] for fn in os.listdir("./belphegor/extensions") if fn.endswith(".py")]
log.debug(f"all extensions: {', '.join(all_extensions)}")
ExtensionChoice = enum.Enum("ExtensionChoice", all_extensions)

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
        extension: ExtensionChoice
    ):
        extension = extension.name

        class ReloadButton(BaseButton[StandardView]):
            label: str = f"Reload {extension}"
            emoji: EmojiType = "\U0001f504"
            style: enums.ButtonStyle = enums.ButtonStyle.primary

            async def callback(self, interaction: Interaction):
                fullname_extension = f"belphegor.extensions.{extension}"
                try:
                    if fullname_extension in interaction.client.extensions:
                        await interaction.client.reload_extension(fullname_extension)
                    else:
                        await interaction.client.load_extension(fullname_extension)
                except commands.ExtensionError:
                    await utils.InteractionHelper.response_to(interaction, content = f"```\nFailed reloading {extension}:\n{traceback.format_exc()}```", view = self.view)
                else:
                    log.info(f"Reloaded {fullname_extension}")
                    await utils.InteractionHelper.response_to(interaction, content = f"```\nSuccess reloading {extension}```", view = self.view)

        view = StandardView()
        reload_button = ReloadButton()
        view.add_item(reload_button)
        view.add_exit_button()
        await reload_button.callback(interaction)

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
                await utils.InteractionHelper.response_to(interaction, embed = embed, view = view)
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
                        await utils.InteractionHelper.response_to(interaction, embed = embed, attachments = [discord.File.from_str(ret, "output.txt")], view = view)
                    else:
                        embed.add_field(name = "Output", value = f"```\n{ret}\n```", inline = False)
                        await utils.InteractionHelper.response_to(interaction, embed = embed, view = view)

    @ac.command(name = "sync")
    @ac.check(Check.owner_only())
    async def sync(
        self,
        interaction: Interaction
    ):
        """
        Sync all commands.
        """
        await interaction.response.defer(thinking = True)
        await self.bot.tree.sync()
        await interaction.followup.send("Synced.")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Admin(bot))