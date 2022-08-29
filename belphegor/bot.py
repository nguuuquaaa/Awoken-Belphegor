import discord
from discord import app_commands as cmds
from discord.ext import commands, tasks
import asyncio
from bson.codec_options import TypeRegistry

from belphegor.db import MongoClientEX, MongoDatabaseEX, MongoEX
from belphegor import utils

#=============================================================================================================================#

class State:
    pass

#=============================================================================================================================#

class Belphegor(commands.Bot):
    mongo: MongoEX
    state: State

    def __init__(self,
        *args,
        initial_extensions: list[str] = ["admin"],
        default_presence: discord.BaseActivity = None,
        **kwargs
    ):
        self.initial_extensions = initial_extensions
        super().__init__(*args, **kwargs)
        self.log = utils.get_logger()

        self.default_presence = default_presence
        self.start_time = utils.now()
        self._counter = 0

    async def setup_hook(self):
        for extension in self.initial_extensions:
            await self.load_extension(f"belphegor.extensions.{extension}")
            self.log.info(f"Done loading {extension}")

        mongo_client = MongoClientEX(
            type_registry = TypeRegistry(fallback_encoder = str),
            tz_aware = True
        )
        self.mongo = MongoEX(
            client = mongo_client,
            db = mongo_client.belphegor_db
        )

    async def on_ready(self):
        self.log.info("Logged in as")
        self.log.info(self.user.name)
        self.log.info(self.user.id)
        self.log.info("----------")
        await asyncio.sleep(5)
        await self.change_presence(activity = self.default_presence)

