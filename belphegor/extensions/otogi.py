import discord
from discord import app_commands as ac
from discord.ext import commands
from pydantic import BaseModel
from typing import Literal, Callable
import functools
import random

from belphegor import utils
from belphegor.utils import wiki
from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction
from belphegor.templates.paginators import SingleRowPaginator, PageItem
from belphegor.templates.views import StandardView
from belphegor.templates.buttons import BaseButton, StatsButton, TriviaButton, SkinsButton

#=============================================================================================================================#

SPECIAL = {
    "Commander Yashichi": ("Yashichi", "prefixed"),
    "Earth Defense Force: Helium": ("Helium Elf", "prefixed"),
    "Malefic: Thorn": ("Thorn", "prefixed"),
    "Wild Star Thorn": ("Thorn", "prefixed")
}

EMOJIS = {
    "phantasma": discord.PartialEmoji(name = "phantasma", id = 308477989228904458),
    "divina": discord.PartialEmoji(name = "divina", id = 308478012956082187),
    "anima": discord.PartialEmoji(name = "anima", id = 308478029062209537),
    "melee": discord.PartialEmoji(name = "melee", id = 306680356751409152),
    "ranged": discord.PartialEmoji(name = "ranged", id = 306680382017896449),
    "healer": discord.PartialEmoji(name = "healer", id = 306680398820147200),
    "assist": discord.PartialEmoji(name = "assist", id = 526446469981536276),
    "mochi": discord.PartialEmoji(name = "mochi", id = 337860563860324354),
    "star": discord.PartialEmoji(name = "star", id = 308476791717101571),
    "atk": discord.PartialEmoji(name = "atk", id = 364913373957062666),
    "hp": discord.PartialEmoji(name = "hp", id = 364913373969907712),
    "skill": discord.PartialEmoji(name = "skill", id = 364913373776969739),
    "ability": discord.PartialEmoji(name = "ability", id = 364913373735026690),
    "bond": discord.PartialEmoji(name = "bond", id = 364913917329276939),
    "invoker": discord.PartialEmoji(name = "invoker", id = 337860298667065345)
}

#=============================================================================================================================#

class DaemonEffect(BaseModel):
    name: str
    effect: str

class DaemonQuote(BaseModel):
    text: str
    url: str | None

class DaemonAllQuotes(BaseModel):
    main: DaemonQuote
    skill: DaemonQuote
    summon: DaemonQuote
    limit_break: DaemonQuote

class Daemon(BaseModel):
    index: int
    name: str
    form: str
    aliases: list[str]
    url: str
    pic_url: str
    artwork_url: str | None
    max_atk: int
    max_hp: int
    mlb_atk: int
    mlb_hp: int
    rarity: int
    daemon_type: Literal["phantasma", "divina", "anima"]
    daemon_class: Literal["melee", "ranged", "healer", "assist"]
    skills: list[DaemonEffect]
    abilities: list[DaemonEffect]
    bonds: list[DaemonEffect]
    faction: str | None
    voice_actor: str | None
    illustrator: str | None
    description: str
    how_to_acquire: str
    notes_and_trivia: str | None
    quotes: DaemonAllQuotes

    def display_stats(self, view: "DaemonView"):
        data_embed = discord.Embed(
            title = f"{EMOJIS[self.daemon_type]} {self.name}",
            description =
                f"{EMOJIS[self.daemon_class]} | {str(EMOJIS['star']) * self.rarity}\n"
                f"{EMOJIS['atk']} {self.max_atk}/{self.mlb_atk}\n{EMOJIS['hp']} {self.max_hp}/{self.mlb_hp}"
                "\n----------------------------------------------------------------------------------",
            colour = discord.Colour.orange()
        )

        for emoji, effects, sep in zip(
            ("skill", "ability", "bond"),
            (self.skills, self.abilities, self.bonds),
            (len(self.abilities) + len(self.bonds) > 0, len(self.bonds) > 0, False)
        ):
            le = len(effects) - 1
            for i, stuff in enumerate(effects):
                if sep and i >= le:
                    data_embed.add_field(
                        name = f"{EMOJIS[emoji]} {stuff.name}",
                        value = f"{stuff.effect}\n----------------------------------------------------------------------------------",
                        inline = False
                    )
                else:
                    data_embed.add_field(
                        name = f"{EMOJIS[emoji]} {stuff.name}",
                        value = stuff.effect,
                        inline = False
                    )

        data_embed.set_image(url = view.images.current())
        return data_embed

    def display_trivia(self, view: "DaemonView"):
        description = self.description or "--"
        des = description.partition(".")
        data_embed = discord.Embed(
            title = f"Wikia: {self.name}",
            description = f"***{des[0]}.***{des[2]}",
            url = self.url,
            colour = discord.Colour.orange()
        )
        data_embed.add_field(name = "Voice Actor", value = self.voice_actor or "--")
        data_embed.add_field(name = "Illustrator", value = self.illustrator or "--")
        data_embed.add_field(name = "How to Acquire", value = self.how_to_acquire or "--", inline = False)
        data_embed.add_field(name = "Notes & Trivia", value = self.notes_and_trivia or "--", inline = False)
        quotes = self.quotes
        data_embed.add_field(
            name = "Quotes",
            value =
                f"Main: [\"{quotes.main.text}\"]({quotes.main.url})\n"
                f"Skill: [\"{quotes.skill.text}\"]({quotes.skill.url})\n"
                f"Summon: [\"{quotes.summon.text}\"]({quotes.summon.url})\n"
                f"Limit break: [\"{quotes.limit_break.text}\"]({quotes.limit_break.url})\n",
            inline = False
        )

        data_embed.set_image(url = view.images.current())
        return data_embed

#=============================================================================================================================#

class OtogiStatsButton(StatsButton["DaemonView"]):
    emoji = discord.PartialEmoji(name = "mochi", id = 337860563860324354)

    async def callback(self, interaction: Interaction):
        view = self.view
        view.embed_display = functools.partial(view.daemon.display_stats, view)
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class OtogiTriviaButton(TriviaButton["DaemonView"]):
    async def callback(self, interaction: Interaction):
        view = self.view
        view.embed_display = functools.partial(view.daemon.display_trivia, view)
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class OtogiImageButton(SkinsButton["DaemonView"]):
    label = "Image"

    async def callback(self, interaction: Interaction):
        view = self.view
        next(view.images)
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class DaemonView(StandardView):
    daemon: Daemon
    images: utils.CircleIter[str]
    embed_display: Callable[[], discord.Embed]

    @classmethod
    def from_daemon(cls, daemon: Daemon):
        view = cls()
        view.daemon = daemon
        view.images = utils.CircleIter([p for p in [daemon.pic_url, daemon.artwork_url] if p], start_index = 0)
        view.embed_display = functools.partial(daemon.display_stats, view)
        view.add_item(OtogiStatsButton())
        view.add_item(OtogiTriviaButton())
        view.add_item(OtogiImageButton())
        view.add_exit_button()
        return view

#=============================================================================================================================#

class OtogiSummonButton(BaseButton):
    label = "Summon"
    emoji = EMOJIS["invoker"]
    style = discord.enums.ButtonStyle.primary

class OtogiSummonResultButton(BaseButton):
    label = "Result"
    emoji = "\U0001f9c2"
    style = discord.enums.ButtonStyle.primary

#=============================================================================================================================#

class Otogi(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot
        self.db = bot.mongo.db

    @ac.command(name = "daemon")
    @ac.describe(name = "Daemon name")
    async def daemon(self, interaction: Interaction, name: str):
        """
        Display a daemon info.
        """
        daemons: dict[str, Daemon] = {}

        async for doc in self.db.otogi_daemons.aggregate([
            {
                "$match": {
                    "$or": utils.QueryHelper.broad_search(name, ("name", "aliases"))
                }
            },
            {
                "$sort": {
                    "name": 1
                }
            },
            {
                "$project": {
                    "_id": 0
                }
            }
        ]):
            daemons[doc["name"]] = Daemon(**doc)

        if len(daemons) == 0:
            return await interaction.response.send_message(f"Can't find any daemon with name: {name}")

        if len(daemons) > 1:
            class DaemonPaginator(SingleRowPaginator):
                class PaginatorSelect(SingleRowPaginator.PaginatorSelect):
                    placeholder = "Select daemon"

                class PaginatorTemplate(SingleRowPaginator.PaginatorTemplate):
                    title = f"Found {len(daemons)} daemons"
                    colour = discord.Colour.orange()

            items = [PageItem(value = dn) for dn in daemons]
            items.sort(key = lambda x: x.value)

            paginator = DaemonPaginator(items = items, page_size = 20)
            async for interaction, value in paginator.setup(interaction, timeout = 180):
                break

            daemon = daemons[value]
            del daemons
            view = DaemonView.from_daemon(daemon)
            await interaction.response.edit_message(embed = daemon.display_stats(view), view = view)
        else:
            daemon = list(daemons.values())[0]
            del daemons
            view = DaemonView.from_daemon(daemon)
            await interaction.response.send_message(embed = daemon.display_stats(view), view = view)

    @ac.command(name = "ls")
    async def lunchsummon(self, interaction: Interaction):
        pool = {doc["rarity"]: doc["pool"] async for doc in self.db.otogi_summon_pool.find({})}

        class SummonOneButton(OtogiSummonButton):
            async def callback(inner_self, interaction: Interaction):
                roll = random.randrange(100)
                if roll < 4:
                    rarity = 5
                elif 4 <= roll < 22:
                    rarity = 4
                else:
                    rarity = 3
                did = random.choice(pool[rarity])
                daemon = await self.db.otogi_daemons.find_one({"index": did}, {"_id": 0, "name": 1, "pic_url": 1})
                inner_self.view.total_summons += 1

                embed = discord.Embed(
                    title = f"{interaction.user.display_name} summoned {daemon['name']}!",
                    colour = discord.Colour.orange()
                )
                embed.set_image(url = daemon["pic_url"])
                embed.set_footer(text = f"Total: {inner_self.view.total_summons} summons")
                response = utils.ResponseHelper(interaction)
                await response.send(embed = embed, view = inner_self.view)

        view = StandardView()
        view.total_summons = 0
        summon = SummonOneButton()
        view.add_item(summon)
        view.add_exit_button()
        await summon.callback(interaction)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Otogi(bot))