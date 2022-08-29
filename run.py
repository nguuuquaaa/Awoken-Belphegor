import discord

from belphegor.bot import Belphegor
from belphegor.settings import settings

#=============================================================================================================================#

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = Belphegor(
    command_prefix = "bel ",
    initial_extensions = [
        "admin",
        "misc"
    ],
    default_presence = discord.Game(name="with Awoken Chronos-senpai"),
    intents = intents
)
bot.run(settings.DISCORD_TOKEN)
