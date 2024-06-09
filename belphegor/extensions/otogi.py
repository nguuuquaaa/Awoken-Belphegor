import discord
from discord import app_commands as ac
from discord.ext import commands
from pydantic import BaseModel
import typing
import functools
import random

from belphegor import utils
from belphegor.utils import wiki
from belphegor.templates import ui_ex, paginators, queries
from belphegor.templates.discord_types import Interaction

if typing.TYPE_CHECKING:
    from belphegor.bot import Belphegor

#=============================================================================================================================#

OTOGI_WIKIA_URL = "https://otogi.wikia.com"

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
    daemon_type: typing.Literal["phantasma", "divina", "anima"]
    daemon_class: typing.Literal["melee", "ranged", "healer", "assist"]
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

    def display_stats(self, paginator: "DaemonDisplay"):
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

        data_embed.set_image(url = paginator.images.current())
        paginator.edit_blueprint(embed = data_embed)
        return paginator

    def display_trivia(self, paginator: "DaemonDisplay"):
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

        data_embed.set_image(url = paginator.images.current())
        paginator.edit_blueprint(embed = data_embed)
        return paginator

#=============================================================================================================================#

class DaemonSelectMenu(paginators.PaginatorSelect):
    async def callback(self, interaction: Interaction):
        old_paginator: DaemonSelector = self.view.panel
        daemon = old_paginator.daemons[self.values[0]]
        new_paginator = DaemonDisplay(daemon)
        new_paginator.target_message = old_paginator.target_message
        old_paginator.stop()
        await new_paginator.initialize(interaction)

class DaemonSelector(paginators.SingleRowPaginator):
    daemons: dict[str, Daemon]

    select_menu: DaemonSelectMenu

    @classmethod
    def from_daemons(cls, daemons: list[Daemon]):
        paginator = cls([paginators.PageItem(value = d.name) for d in daemons], selectable = True)
        paginator.daemons = {d.name: d for d in daemons}
        return paginator

    def render_embed(self):
        embed = super().render_embed()
        embed.title = f"Found {len(self.daemons)} daemons"
        return embed

#=============================================================================================================================#

class DaemonStatsButton(ui_ex.StatsButton):
    emoji = discord.PartialEmoji(name = "mochi", id = 337860563860324354)

    paginator: "DaemonDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.render = functools.partial(paginator.daemon.display_stats, paginator)
        await paginator.update(interaction)

class DaemonTriviaButton(ui_ex.TriviaButton):
    paginator: "DaemonDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.render = functools.partial(paginator.daemon.display_trivia, paginator)
        await paginator.update(interaction)

class DaemonImageButton(ui_ex.SkinsButton):
    label = "Image"

    paginator: "DaemonDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        next(paginator.images)
        await paginator.update(interaction)

class DaemonDisplay(paginators.BasePaginator):
    daemon: Daemon
    images: utils.CircleIter[str]

    stats_button: DaemonStatsButton
    trivia_button: DaemonTriviaButton
    image_button: DaemonImageButton

    def __init__(self, daemon: Daemon):
        self.daemon = daemon
        self.images = utils.CircleIter([p for p in [daemon.pic_url, daemon.artwork_url] if p], start_index = 0)
        self.render = functools.partial(daemon.display_stats, self)

        view = self.view = ui_ex.View()
        view.add_item(self.get_paginator_attribute("stats_button", row = 0))
        view.add_item(self.get_paginator_attribute("trivia_button", row = 0))
        view.add_item(self.get_paginator_attribute("image_button", row = 0))
        view.add_exit_button(row = 1)

#=============================================================================================================================#

class SummonButton(ui_ex.Button):
    label = "Summon"
    emoji = EMOJIS["invoker"]
    style = discord.enums.ButtonStyle.primary

    paginator: "ContinuousSummon"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator

        roll = random.randrange(100)
        if roll < 4:
            rarity = 5
        elif 4 <= roll < 22:
            rarity = 4
        else:
            rarity = 3
        d = random.choice(paginator.pool[rarity])
        paginator.total_summons += 1

        embed = discord.Embed(
            title = f"{interaction.user.display_name} summoned {d['name']}!",
            colour = discord.Colour.orange(),
            url = OTOGI_WIKIA_URL
        )
        embed.set_image(url = d["pic_url"])
        embed.set_footer(text = f"Total: {paginator.total_summons} summons")

        paginator.edit_blueprint(embed = embed, embeds = None)
        await paginator.update(interaction)

class Summon10Button(ui_ex.Button):
    label = "x10 summon"
    emoji = EMOJIS["invoker"]
    style = discord.enums.ButtonStyle.primary

    paginator: "ContinuousSummon"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator

        result = []
        for _ in range(10):
            roll = random.randrange(100)
            if roll < 4:
                rarity = 5
            elif 4 <= roll < 22:
                rarity = 4
            else:
                rarity = 3
            result.append(random.choice(paginator.pool[rarity]))
        paginator.total_summons += 10

        embed = discord.Embed(
            title = f"{interaction.user.display_name} summoned 10 times!",
            colour = discord.Colour.orange(),
            description = "\n".join(d["name"] for d in result),
            url = OTOGI_WIKIA_URL
        )
        embed.set_image(url = result[0]["pic_url"])
        embed.set_footer(text = f"Total: {paginator.total_summons} summons")
        embeds = [embed]

        for d in result[1:]:
            embed = discord.Embed(url = OTOGI_WIKIA_URL)
            embed.set_image(url = d["pic_url"])
            embeds.append(embed)

        paginator.edit_blueprint(embed = None, embeds = embeds)
        await paginator.update(interaction)

class ContinuousSummon(paginators.BasePaginator):
    pool: dict[int, list[dict[str]]]
    total_summons: int

    summon_button: SummonButton

    @classmethod
    def from_pool(cls, pool: dict[int, list[dict[str]]]):
        paginator = cls()
        paginator.pool = pool
        paginator.total_summons = 0
        return paginator

    def render(self):
        if not self.view:
            view = self.view = ui_ex.View()
            self.summon_button = self.get_paginator_attribute("summon_button")
            view.add_item(self.summon_button)
            view.add_exit_button()

        return self

    async def initialize(self, interaction: Interaction):
        panel = self.render()
        panel.view.allowed_user = interaction.user
        await self.summon_button.callback(interaction)

#=============================================================================================================================#

class Otogi(commands.Cog):
    def __init__(self, bot: "Belphegor"):
        self.bot = bot
        self.db = bot.mongo.db

    @ac.command(name = "daemon")
    @ac.describe(name = "Daemon name")
    async def daemon(self, interaction: Interaction, name: str):
        """
        Display a daemon info.
        """
        daemons = []

        async for doc in self.db.otogi_daemons.aggregate([
            {
                "$match": queries.match_any(name, ["name", "aliases"])
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
            daemons.append(Daemon(**doc))

        if len(daemons) == 0:
            return await interaction.response.send_message(f"Can't find any daemon with name: {name}")

        if len(daemons) > 1:
            paginator = DaemonSelector.from_daemons(daemons)
            await paginator.initialize(interaction)
        else:
            paginator = DaemonDisplay(daemons[0])
            await paginator.initialize(interaction)

    @ac.command(name = "ls")
    async def lunchsummon(self, interaction: Interaction):
        pool = {}
        async for doc in self.db.otogi_summon_pool.aggregate([
            {
                "$unwind": "$pool"
            },
            {
                "$lookup": {
                    "from": "otogi_daemons",
                    "localField": "pool",
                    "foreignField": "index",
                    "as": "daemon"
                }
            },
            {
                "$group": {
                    "_id": "$rarity",
                    "pool": {
                        "$push": {
                            "name": {
                                "$arrayElemAt": [
                                    "$daemon.name",
                                    0
                                ]
                            },
                            "pic_url": {
                                "$arrayElemAt": [
                                    "$daemon.pic_url",
                                    0
                                ]
                            }
                        }
                    }
                }
            }
        ]):
            pool[doc["_id"]] = doc["pool"]

        cont_summon = ContinuousSummon.from_pool(pool)
        await cont_summon.initialize(interaction)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Otogi(bot))