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

from belphegor import utils
from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction, File
from belphegor.errors import FlowControl
from belphegor.templates.buttons import BaseButton, EmojiType
from belphegor.templates.views import ContinuousInputView, StandardView
from belphegor.templates.checks import Check

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
                response = utils.ResponseHelper(interaction)
                try:
                    if fullname_extension in interaction.client.extensions:
                        await interaction.client.reload_extension(fullname_extension)
                    else:
                        await interaction.client.load_extension(fullname_extension)
                except commands.ExtensionError:
                    await response.send(content = f"```\nFailed reloading {extension}:\n{traceback.format_exc()}```", view = self.view)
                else:
                    log.info(f"Reloaded {fullname_extension}")
                    await response.send(content = f"```\nSuccess reloading {extension}```", view = self.view)

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
        try:
            m = importlib.import_module(f"belphegor.{module}")
            importlib.reload(m)
        except :
            traceback.print_exc()
            await interaction.response.send_message(f"```\nFailed reimporting: {module}```")
        else:
            print(f"Reimported belphegor.{module}")
            await interaction.response.send_message(f"```\nSuccess reimporting: {module}```")

    @ac.command(name = "eval")
    @ac.check(Check.owner_only())
    async def _eval(
        self,
        interaction: Interaction
    ):
        view = ContinuousInputView(allowed_user = interaction.user)
        async for interaction, input in view.setup(interaction):
            response = utils.ResponseHelper(interaction)
            await response.thinking()

            try:
                code = f"async def func():\n{textwrap.indent(input.value, '    ')}"
                env = {
                    "bot": self.bot,
                    "interaction": interaction,
                    "response": response,
                    "discord": discord,
                    "utils": utils,
                    "asyncio": asyncio
                }

                try:
                    exec(code, env)
                except Exception as e:
                    raise FlowControl({"input": input.value, "output": str(e)})

                stdout = StringIO()
                func = env["func"]
                try:
                    with redirect_stdout(stdout):
                        await func()
                except:
                    add_text = f"\n{traceback.format_exc()}"
                else:
                    add_text = ""
                finally:
                    raise FlowControl({"input": input.value, "output": (stdout.getvalue() + add_text).strip()})

            except FlowControl as e:
                iv = e.message["input"]
                ov = e.message["output"]
                if len(iv) > 1000 or len(ov) > 1000:
                    await response.send(
                        files = [
                            File.from_str(iv, "input.py"),
                            File.from_str(ov, "output.txt")
                        ],
                        view = view
                    )
                else:
                    embed = discord.Embed()
                    embed.add_field(name = "Input", value = f"```py\n{iv}\n```", inline = False)
                    embed.add_field(name = "Output", value = f"```\n{ov}\n```", inline = False)
                    await response.send(
                        embed = embed,
                        view = view
                    )

    @ac.command(name = "sync")
    @ac.check(Check.owner_only())
    async def sync(
        self,
        interaction: Interaction,
        scope: typing.Literal["guild", "global"] = "global",
        guild_id: str = None
    ):
        """
        Sync all commands.
        """
        await interaction.response.defer(thinking = True)
        match scope:
            case "guild":
                if guild_id is None:
                    await self.bot.tree.sync(guild = interaction.guild)
                else:
                    await self.bot.tree.sync(guild = discord.Object(int(guild_id)))
            case "global":
                await self.bot.tree.sync()

        await interaction.followup.send("Synced.")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Admin(bot))