import discord
from discord import app_commands as ac
from discord.ext import commands
import asyncio
from bson.codec_options import TypeRegistry
import traceback
import aiohttp
import redis.asyncio as aredis

from belphegor import utils
from belphegor.db import MongoClientEX, MongoEX

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

class State:
    def setdefault(self, key, value):
        try:
            return getattr(self, key)
        except AttributeError:
            setattr(self, key, value)
            return value

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

        self.default_presence = default_presence
        self.start_timestamp = utils.now()
        self.state = State()
        self.session: aiohttp.ClientSession = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        mongo_client = MongoClientEX(
            host = "mongodb",
            port = 27017,
            type_registry = TypeRegistry(fallback_encoder = str),
            tz_aware = True
        )
        self.mongo = MongoEX(
            client = mongo_client,
            db = mongo_client.belphegor_db
        )

        self.redis = aredis.Redis(host = "redis")

        for extension in self.initial_extensions:
            await self.load_extension(f"belphegor.extensions.{extension}")
            log.info(f"Done loading {extension}")

    async def on_ready(self):
        self.owner_id = self.application.owner.id
        log.info("Logged in as")
        log.info(self.user.name)
        log.info(self.user.id)
        log.info("----------")
        await asyncio.sleep(5)
        await self.change_presence(activity = self.default_presence)

    async def on_error(self, event, /, *args, **kwargs):
        log.error(f"{event} - args: {args} - kwargs: {kwargs}\n{traceback.format_exc()}")

    async def get_prefix(self, message: discord.Message):
        return [f"<@{self.user.id}> ", f"<@!{self.user.id}> "]

    async def close(self):
        await super().close()
        await self.session.close()
        await self.redis.aclose()
