import discord
from discord import app_commands as ac
from discord.ext import commands
import importlib
import sys
import traceback
import textwrap
import asyncio
from io import StringIO, BytesIO
from contextlib import redirect_stdout
import os
import typing
import enum
from yarl import URL
from email.message import Message

from belphegor import utils
from belphegor.settings import settings
from belphegor.bot import Belphegor
from belphegor.errors import FlowControl
from belphegor.templates import checks, panels, transformers
from belphegor.templates.discord_types import Interaction, File

#=============================================================================================================================#

log = utils.get_logger()
all_extensions = [fn[:-3] for fn in os.listdir("./belphegor/extensions") if fn.endswith(".py")]
log.debug(f"All extensions: {', '.join(all_extensions)}")
ExtensionChoice = enum.Enum("ExtensionChoice", all_extensions)

#=============================================================================================================================#

class Admin(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @ac.command(name = "reload")
    @ac.describe(extension = "Extension to reload")
    @ac.guilds(*settings.TEST_GUILDS)
    @ac.check(checks.owner_only())
    async def reload(
        self,
        interaction: Interaction,
        extension: ExtensionChoice
    ):
        panel = panels.ControlPanel()
        await panel.thinking(interaction)
        extension = extension.name
        fullname_extension = f"belphegor.extensions.{extension}"
        try:
            if fullname_extension in interaction.client.extensions:
                await interaction.client.reload_extension(fullname_extension)
            else:
                await interaction.client.load_extension(fullname_extension)
        except commands.ExtensionError:
            panel.edit_blueprint(content = f"```\nFailed reloading {extension}:\n{traceback.format_exc()}```")
        else:
            log.info(f"Reloaded {fullname_extension}")
            panel.edit_blueprint(content = f"```\nSuccess reloading {extension}```")

        await panel.reply(interaction)

    @ac.command(name = "reimport")
    @ac.describe(module = "Module to reimport")
    @ac.guilds(*settings.TEST_GUILDS)
    @ac.check(checks.owner_only())
    async def reimport(
        self,
        interaction: Interaction,
        module: str
    ):
        panel = panels.ControlPanel()
        await panel.thinking(interaction)
        try:
            m = importlib.import_module(f"belphegor.{module}")
            importlib.reload(m)
        except :
            traceback.print_exc()
            panel.edit_blueprint(content = f"```\nFailed reimporting: {module}```")
        else:
            print(f"Reimported belphegor.{module}")
            panel.edit_blueprint(content = f"```\nSuccess reimporting: {module}```")

        await panel.reply(interaction)

    @commands.command(name = "eval")
    @commands.is_owner()
    async def eval_(self, ctx, *, raw: str):
        base_code = utils.clean_codeblock(raw)
        code = f"async def func():\n{textwrap.indent(base_code, '    ')}"
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "discord": discord,
            "commands": commands,
            "utils": utils,
            "asyncio": asyncio
        }

        try:
            try:
                exec(code, env)
            except Exception as e:
                raise FlowControl(str(e))

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
                raise FlowControl((stdout.getvalue() + add_text).strip())

        except FlowControl as e:
            iv = base_code
            ov = e.message
            if len(iv) > 1000 or len(ov) > 1000:
                await ctx.send(files = [
                    File.from_str(iv, "input.py"),
                    File.from_str(ov, "output.txt")
                ])
            else:
                embed = discord.Embed()
                embed.add_field(name = "Input", value = f"```py\n{iv}\n```", inline = False)
                embed.add_field(name = "Output", value = f"```\n{ov}\n```", inline = False)
                await ctx.send(embed = embed)

    @commands.command(name = "sync")
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        scope: typing.Literal["guild", "guilds", "global"] = "global",
        *guild_ids: int
    ):
        async with ctx.typing():
            await self.bot.tree.sync()
            match scope:
                case "guild" | "guilds":
                    if guild_ids:
                        for guild_id in guild_ids:
                            await self.bot.tree.sync(guild = discord.Object(guild_id))
                    else:
                        for guild_id in settings.TEST_GUILDS:
                            await self.bot.tree.sync(guild = discord.Object(guild_id))
                case "global":
                    await self.bot.tree.sync()
        await ctx.send("Synced.")

    @ac.command(name = "download")
    @ac.guilds(*settings.TEST_GUILDS)
    @ac.check(checks.owner_only())
    async def download(
        self,
        interaction: Interaction,
        url: ac.Transform[URL, transformers.URLTransformer]
    ):
        chunk_size = 1024 * 1024
        await interaction.response.defer(thinking = True)
        async with self.bot.session.get(url, headers = {"User-Agent": settings.USER_AGENT}) as resp:
            log.debug(resp.headers)
            m = Message()
            m["content-type"] = resp.content_disposition
            filename = m.get_param("filename")
            if filename is None:
                filename = "file"

            b = BytesIO()
            async for chunk in resp.content.iter_chunked(chunk_size):
                b.write(chunk)

        b.seek(0)
        await interaction.followup.send(file = discord.File(b, filename = filename))

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Admin(bot))
