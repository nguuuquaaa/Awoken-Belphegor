import discord
from discord import app_commands
from discord.ext import tasks
import asyncio

from belphegor.db import MongoClientEX
from belphegor.cogs import misc

#=============================================================================================================================#

class Belphegor(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = MongoClientEX()
        self.db = self.db_client.woke_bel_db

        self.tree = app_commands.CommandTree(self)
        misc.setup(self.tree)

        for cmd in self.tree.walk_commands():
            print(cmd)

    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("------")
        await asyncio.sleep(5)
        await self.tree.sync()
        await self.change_presence(activity=discord.Game(name="with bugs"))