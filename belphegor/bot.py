import discord
from discord import app_commands as cmds
from discord.ext import commands, tasks
import asyncio

from belphegor.db import MongoClientEX
from belphegor import utils

#=============================================================================================================================#

class Belphegor(commands.Bot):
    def __init__(self, *args, default_presence: discord.BaseActivity = None, **kwargs):
        self.initial_extensions = kwargs.pop("extensions")
        super().__init__(*args, **kwargs)
        self.db_client = MongoClientEX()
        self.db = self.db_client.woke_bel_db

        self.default_presence = default_presence
        self.startup_event = asyncio.Event()
        self.start_time = utils.now()
        self._counter = 0

    async def sync_commands(self):
        await self.startup_event.wait()
        for extension in self.initial_extensions:
            await self.load_extension(f"belphegor.cogs.{extension}")
            print(f"Done loading {extension}")
        await self.tree.sync()
        print("Done syncing")

    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
        await asyncio.sleep(5)
        self.startup_event.set()
        await self.change_presence(activity = self.default_presence)

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        asyncio.create_task(self.sync_commands())
        return await super().start(token, reconnect=reconnect)

    def counter(self):
        self._counter += 1
        return self._counter
