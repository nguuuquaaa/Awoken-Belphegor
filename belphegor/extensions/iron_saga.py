import discord
from discord import app_commands as ac
from discord.ext import commands
from pydantic import BaseModel, Field
import typing
from collections.abc import Callable
from urllib.parse import quote
import json
from functools import partial
import time
import traceback

from belphegor import errors, utils
from belphegor.utils import CircleIter, grouper, wiki
from belphegor.templates import ui_ex, paginators, queries, checks
from belphegor.templates.discord_types import Interaction, File

if typing.TYPE_CHECKING:
    from belphegor.bot import Belphegor

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

ISWIKI_BASE = "https://ironsaga.fandom.com"
ISWIKI_API = f"{ISWIKI_BASE}/api.php"

COPILOT_SLOTS = {
    "attack": "Attack",
    "tech": "Tech",
    "defense": "Defense",
    "support": "Support",
    "control": "Control",
    "special": "Special"
}

#=============================================================================================================================#

parser = wiki.WikitextParser()

@parser.set_box_handler("PilotInfo")
@parser.set_box_handler("PilotInfo1")
def handle_base_box(box, **kwargs):
    return {"pilot_info": kwargs}

@parser.set_box_handler("PilotIcon")
def handle_icon_box(box, name, *args, **kwargs):
    return name

@parser.set_html_handler
def handle_html(tag, text, **kwargs):
    if tag == "tabber":
        return {"tabber": text}
    elif tag == "gallery":
        return {"skin_gallery": text.strip().splitlines()}
    else:
        return text

@parser.set_reference_handler
def handle_reference(box, *args, **kwargs):
    if box.startswith("File:"):
        return {"file": box[5:]}
    else:
        return box

#=============================================================================================================================#

PilotPersonality: typing.TypeAlias = typing.Literal[
    "Brave",
    "Calm",
    "Energetic",
    "Extreme",
    "Friendly",
    "Gentle",
    "Impatient",
    "Lazy",
    "Mighty",
    "Normal",
    "Peaceful",
    "Rational",
    "Sensitive",
    "Timid"
]

class PilotStats(BaseModel):
    melee: int = Field(..., gt = 0)
    ranged: int = Field(..., gt = 0)
    defense: int = Field(..., gt = 0)
    reaction: int = Field(..., gt = 0)

class PilotSkill(BaseModel):
    name: str = Field(..., min_length = 1)
    effect: str = Field(..., min_length = 1)
    copilot: str | None

class PilotSkin(BaseModel):
    name: str = Field(..., min_length = 1)
    url: str = Field(..., min_length = 1)

    @classmethod
    def from_filename(cls, filename: str) -> dict:
        name = filename[:-4].replace("_", " ").replace(" Render", "")
        return cls.construct(
            name = name,
            url = f"{ISWIKI_BASE}/{wiki.generate_image_path(filename)}"
        )

class PilotCopilotSlots(BaseModel):
    Attack: bool
    Tech: bool
    Defense: bool
    Support: bool
    Control: bool
    Special: bool

class Pilot(BaseModel):
    index: int
    en_name: str = Field(..., min_length = 1)
    jp_name: str
    page_name: str = Field(..., min_length = 1)
    faction: str
    stats: PilotStats
    personality: PilotPersonality
    copilot_slots: PilotCopilotSlots
    skills: tuple[PilotSkill, PilotSkill, PilotSkill, PilotSkill]
    artist: str | None
    voice_actor: str | None
    description: str | None
    skins: list[PilotSkin]

    def display_stats_info(self, paginator: "PilotDisplay"):
        embed = discord.Embed(
            title = self.en_name or self.page_name,
            color = discord.Color.red(),
            url = f"{ISWIKI_BASE}/wiki/{quote(self.page_name)}"
        )

        stats = self.stats
        embed.add_field(
            name = "Stats",
            value = f"Melee: {stats.melee}\n"
                f"Ranged: {stats.ranged}\n"
                f"Defense: {stats.defense}\n"
                f"Reaction: {stats.reaction}"
        )

        embed.add_field(name = "Personality", value = self.personality)
        embed.add_field(name = "Copilot slots", value = " | ".join(k for k, v in self.copilot_slots.dict().items() if v), inline = False)

        for sk, dot in zip(self.skills, ["\u25CF", "\u00B7", "\u00B7", "\u00B7"]):
            copilot = sk.copilot
            if copilot:
                copilot = f" [{copilot}]"
            else:
                copilot = ""
            embed.add_field(
                name=f"{dot} {sk.name}{copilot}",
                value=sk.effect,
                inline=False
            )

        skin = paginator.skins.current().current()
        paginator.skin_select.placeholder = skin.name
        embed.set_image(url = skin.url)

        paginator.panel.embed = embed
        return paginator.panel

    def display_other_info(self, paginator: "PilotDisplay"):
        embed = discord.Embed(
            title = self.en_name or self.page_name,
            description = self.description or "N/A",
            color = discord.Color.red(),
            url = f"{ISWIKI_BASE}/wiki/{quote(self.page_name)}"
        )
        embed.add_field(name = "Faction", value = self.faction, inline=False)
        embed.add_field(name = "Artist", value = self.artist or "N/A")
        embed.add_field(name = "Voice actor", value = self.voice_actor or "N/A")

        skin = paginator.skins.current().current()
        paginator.skin_select.placeholder = skin.name
        embed.set_image(url = skin.url)

        paginator.panel.embed = embed
        return paginator.panel

class PilotReductSkills(Pilot):
    skills: tuple[PilotSkill, ...]

#=============================================================================================================================#

class PilotSelectMenu(paginators.PaginatorSelect):
    paginator: "PilotSelector"

    async def callback(self, interaction: Interaction):
        pilot = self.paginator.pilots[self.values[0]]
        paginator = PilotDisplay(pilot)
        await paginator.initialize(interaction)

class PilotSelector(paginators.SingleRowPaginator):
    pilots: dict[str, Pilot]

    select_menu: PilotSelectMenu

    @classmethod
    def from_pilots(cls, pilots: list[Pilot]):
        paginator = cls([paginators.PageItem(value = p.en_name) for p in pilots], selectable = True)
        paginator.pilots = {p.en_name: p for p in pilots}
        return paginator

    def create_embed(self):
        embed = super().create_embed()
        embed.title = f"Found {len(self.pilots)} pilots"
        return embed

#=============================================================================================================================#

class ISStatsButton(ui_ex.StatsButton):
    emoji = discord.PartialEmoji(name = "exp_capsule", id = 824327490536341504)

    paginator: "PilotDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.render = partial(paginator.pilot.display_stats_info, paginator)
        await paginator.update(interaction)

class ISTriviaButton(ui_ex.TriviaButton):
    paginator: "PilotDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.render = partial(paginator.pilot.display_other_info, paginator)
        await paginator.update(interaction)

class ISSkinsButton(ui_ex.SkinsButton):
    paginator: "PilotDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.show_next_skin_set()
        await paginator.update(interaction)

class ISSkinSelect(ui_ex.SelectOne):
    placeholder = "Select skin to display"

    paginator: "PilotDisplay"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        result = self.values[0]
        paginator.skins.current().jump_to(int(result))
        await paginator.update(interaction)

class PilotDisplay(paginators.BasePaginator):
    SKIN_SELECT_SIZE = 20

    pilot: Pilot
    skins: CircleIter[CircleIter[PilotSkin]]

    stat_button: ISStatsButton
    trivia_button: ISTriviaButton
    skin_button: ISSkinsButton
    skin_select: ISSkinSelect

    def __init__(self, pilot: Pilot):
        super().__init__()
        self.pilot = pilot
        self.skins = CircleIter([CircleIter(s, start_index = 0) for s in grouper(pilot.skins, self.SKIN_SELECT_SIZE, incomplete = "missing")], start_index = -1)
        self.render = partial(self.pilot.display_stats_info, self)

        view = ui_ex.StandardView()
        view.add_item(self.get_paginator_attribute("stat_button", row = 1))
        view.add_item(self.get_paginator_attribute("trivia_button", row = 1))
        view.add_item(self.get_paginator_attribute("skin_button", row = 1))
        view.add_exit_button(row = 1)
        self.panel.view = view

        self.show_next_skin_set()

    def show_next_skin_set(self):
        if getattr(self, "skin_select", None):
            self.remove_item(self.skin_select)

        next(self.skins)
        set_index, batch = self.skins.current(True)
        batch.jump_to(0)
        skin_select = self.get_paginator_attribute("skin_select", row = 0)
        for i, skin in enumerate(batch.iter_once()):
            skin_select.add_option(
                label = f"{set_index * self.SKIN_SELECT_SIZE + i + 1}. {skin.name}",
                value = str(i)
            )
        self.skin_select = skin_select
        self.panel.view.add_item(skin_select)

#=============================================================================================================================#

class SkillEmbedTemplate(paginators.PaginatorEmbedTemplate):
    description: str | Callable | None = None
    fields: Callable = lambda item, index: (
        item.value.en_name,
        f"**{item.value.skills[0].name} {'[' + item.value.skills[0].copilot + ']' if item.value.skills[0].copilot else ''}**\n{item.value.skills[0].effect}",
        False
    )

class SkillPaginator(PilotSelector):
    embed_template: SkillEmbedTemplate

    @classmethod
    def from_pilots(cls, pilots: list[PilotReductSkills]):
        paginator = cls([paginators.PageItem(value = p) for p in pilots], page_size = 5, selectable = False)
        paginator.pilots = {p.en_name: p for p in pilots}
        return paginator

#=============================================================================================================================#

COLOR_MAPPING = {
    "S": discord.Color.purple(),
    "A": discord.Color.blue(),
    "B": discord.Color.green(),
    "C": discord.Color.light_grey()
}

class Part(BaseModel):
    name: str
    classification: typing.Literal["core", "shell", "support", "armour", "coating"]
    rank: typing.Literal["S", "A", "B", "C"]
    effect: str
    thumbnail: str
    aliases: list[str] = []

    def display(self):
        embed = discord.Embed(
            title = f"[{self.classification.capitalize()}] {self.name}",
            description = self.effect,
            color = COLOR_MAPPING[self.rank]
        )
        embed.set_thumbnail(url = self.thumbnail)
        return embed

#=============================================================================================================================#

class PartSelectMenu(paginators.PaginatorSelect):
    paginator: "PartSelector"

    def add_items_as_options(self, items: list[paginators.PageItem[Part]], current_index: int):
        for i, item in enumerate(items):
            self.add_option(
                label = f"{i + current_index + 1}. {item.value.name}",
                value = f"{item.value.rank}_{item.value.name}"
            )

    async def callback(self, interaction: Interaction):
        part = self.paginator.parts[self.values[0]]
        panel = self.paginator.panel
        panel.stop()
        panel.view = None
        panel.embed = part.display()
        await panel.reply(interaction)

class PartEmbedTemplate(paginators.PaginatorEmbedTemplate):
    description: Callable[[paginators.PageItem, int], str] = lambda item, index: f"{index + 1}. [{item.value.rank}] {item.value.name}"

class PartSelector(paginators.SingleRowPaginator):
    parts: dict[str, Part]

    select_menu: PartSelectMenu
    embed_template: PartEmbedTemplate

    @classmethod
    def from_parts(cls, parts: list[Part]):
        paginator = cls([paginators.PageItem(value = p) for p in parts], selectable = True)
        paginator.parts = {f"{p.rank}_{p.name}": p for p in parts}
        return paginator

    def create_embed(self):
        embed = super().create_embed()
        embed.title = f"Found {len(self.parts)} parts"
        return embed

#=============================================================================================================================#

class Pet(BaseModel):
    name: str
    effect: str
    thumbnail: str
    aliases: list[str] = []

    def display(self):
        embed = discord.Embed(
            title = self.name,
            description = self.effect,
            color = discord.Color.purple()
        )
        embed.set_thumbnail(url = self.thumbnail)
        return embed

#=============================================================================================================================#

class PetSelectMenu(paginators.PaginatorSelect):
    paginator: "PetSelector"

    async def callback(self, interaction: Interaction):
        pet = self.paginator.pets[self.values[0]]
        panel = self.paginator.panel
        panel.stop()
        panel.view = None
        panel.embed = pet.display()
        await panel.reply(interaction)

class PetSelector(paginators.SingleRowPaginator):
    pets: dict[str, Pet]

    select_menu: PetSelectMenu

    @classmethod
    def from_pets(cls, pets: list[Pet]):
        paginator = cls([paginators.PageItem(value = p.name) for p in pets], selectable = True)
        paginator.pets = {p.name: p for p in pets}
        return paginator

    def create_embed(self):
        embed = super().create_embed()
        embed.title = f"Found {len(self.pets)} pets"
        return embed

#=============================================================================================================================#

class IronSaga(commands.Cog):
    def __init__(self, bot: "Belphegor"):
        self.bot = bot

    @ac.command(name = "pilot")
    @ac.describe(name = "Pilot name")
    async def get_pilot(self, interaction: Interaction, name: str):
        pilots = []
        async for doc in self.bot.mongo.db.iron_saga_pilots.aggregate([
            {
                "$match": queries.match_any(name, ("en_name", "jp_name", "aliases"))
            },
            {
                "$sort": {
                    "en_name": 1
                }
            },
            {
                "$project": {
                    "_id": 0
                }
            }
        ]):
            pilots.append(Pilot(**doc))

        if len(pilots) == 0:
            return await interaction.response.send_message(f"Can't find any pilot with name: {name}")

        if len(pilots) > 1:
            paginator = PilotSelector.from_pilots(pilots)
            await paginator.initialize(interaction)
        else:
            paginator = PilotDisplay(pilots[0])
            await paginator.initialize(interaction)

    @ac.command(name = "skill")
    @ac.describe(name = "Skill name")
    async def skill(self, interaction: Interaction, name: str):
        pilots = []
        async for doc in self.bot.mongo.db.iron_saga_pilots.aggregate([
            {
                "$match": {
                    "skills": {
                        "$elemMatch": queries.match_any(name, ["name", "effect"])
                    }
                }
            },
            {
                "$sort": {
                    "en_name": 1
                }
            },
            {
                "$addFields": {
                    "_id": "$$REMOVE",
                    "skills": {
                        "$filter": {
                            "input": "$skills",
                            "cond": queries.aggregate_match_any(name, ["$$this.name", "$$this.effect"])
                        }
                    }
                }
            }
        ]):
            pilots.append(PilotReductSkills(**doc))

        if pilots:
            paginator = SkillPaginator.from_pilots(pilots)
            await paginator.initialize(interaction)
        else:
            return await interaction.response.send_message(f"Can't find any skill with name: {name}")

    @ac.command(name = "part")
    @ac.describe(name = "Part name")
    async def get_part(self, interaction: Interaction, name: str):
        parts = []
        async for doc in self.bot.mongo.db.iron_saga_parts.aggregate([
            {
                "$match": queries.match_any(name, ("name", "aliases"))
            },
            {
                "$addFields": {
                    "_rank_index": {
                        "$indexOfArray": [
                            ["S", "A", "B", "C"],
                            "$rank"
                        ]
                    }
                }
            },
            {
                "$sort": {
                    "_rank_index": 1,
                    "name": 1
                }
            },
            {
                "$addFields": {
                    "_id": "$$REMOVE",
                    "_rank_index": "$$REMOVE"
                }
            }
        ]):
            parts.append(Part(**doc))

        if len(parts) == 0:
            return await interaction.response.send_message(f"Can't find any part with name: {name}")

        if len(parts) > 1:
            paginator = PartSelector.from_parts(parts)
            await paginator.initialize(interaction)
        else:
            await interaction.response.send_message(embed = parts[0].display())

    @ac.command(name = "pet")
    @ac.describe(name = "Pet name")
    async def get_pet(self, interaction: Interaction, name: str):
        pets = []
        async for doc in self.bot.mongo.db.iron_saga_pets.aggregate([
            {
                "$match": queries.match_any(name, ("name", "aliases"))
            },
            {
                "$sort": {
                    "name": 1
                }
            },
            {
                "$addFields": {
                    "_id": "$$REMOVE"
                }
            }
        ]):
            pets.append(Pet(**doc))

        if len(pets) == 0:
            return await interaction.response.send_message(f"Can't find any pet with name: {name}")

        if len(pets) > 1:
            paginator = PetSelector.from_pets(pets)
            await paginator.initialize(interaction)
        else:
            await interaction.response.send_message(embed = pets[0].display())

    update = ac.Group(name = "update", description = "Update database")

    @update.command(name = "pilot")
    @ac.check(checks.owner_only())
    async def update_pilot(self, interaction: Interaction, name: typing.Optional[str] = None):
        await interaction.response.defer(thinking = True)
        if name is None:
            params = {
                "action":       "parse",
                "prop":         "wikitext",
                "page":         "Pilot_List",
                "format":       "json",
                "redirects":    1
            }
            resp = await self.bot.session.get(ISWIKI_API, params = params)
            raw = json.loads(await resp.content.read())
            data = parser.parse(raw["parse"]["wikitext"]["*"])
            names = []
            for row in data[0]:
                if len(row) > 1:
                    value = row[1].rpartition("<br>")[2].strip()
                    ret = parser.parse(value)
                    names.append(ret)
        else:
            names = [n.strip() for n in name.split(";")]

        progress_bar = utils.ProgressBar(
            progress_message = f"Total: {len(names)} pilots\nFetching...",
            done_message = f"Total: {len(names)} pilots\nDone."
        )

        msg = await interaction.followup.send(progress_bar.progress(0), wait = True)

        passed = []
        failed = []
        errors = {}
        count = len(names)
        prev = time.perf_counter()
        col = self.bot.mongo.db.iron_saga_pilots
        for i, name in enumerate(names):
            try:
                pilot = await self.search_iswiki_for_pilot(name)
            except:
                errors[name] = traceback.format_exc()
                failed.append(name)
            else:
                passed.append(pilot.en_name)
                index = pilot.index
                await col.update_one(
                    {
                        "index": index
                    },
                    {
                        "$set": pilot.dict(),
                        "$setOnInsert": {
                            "aliases": []
                        }
                    },
                    upsert = True
                )
            finally:
                cur = time.perf_counter()
                if cur - prev >= 5:
                    await msg.edit(content = progress_bar.progress((i + 1) / count))
                    prev = cur

        await msg.edit(
            content = f"Passed: {len(passed)}\nFailed: {len(failed)}",
            attachments = [
                File.from_str(json.dumps({"passed": passed, "failed": failed}, indent=4, ensure_ascii=False), "result.json"),
                File.from_str(json.dumps(errors, indent=4, ensure_ascii=False), "errors.json")
            ]
        )

    async def search_iswiki_for_pilot(self, name):
        resp = await self.bot.session.get(
            ISWIKI_API,
            params = {
                "action":       "parse",
                "prop":         "wikitext",
                "page":         name,
                "format":       "json",
                "redirects":    1
            }
        )
        raw = json.loads(await resp.content.read())
        if "error" in raw:
            raise errors.QueryFailed(f"Page {name} doesn't exist.")

        page_id = raw["parse"]["pageid"]
        raw_basic_info = raw["parse"]["wikitext"]["*"]
        ret = parser.parse(raw_basic_info)
        skins: dict[str, PilotSkin] = {}
        for item in ret:
            if isinstance(item, dict):
                skin_galleries = []

                if "pilot_info" in item:
                    basic_info = item["pilot_info"]
                    elem = basic_info["image"]
                    try:
                        tabber = elem[0]["tabber"]
                    except KeyError:
                        filename = elem[0]["file"]
                        skins.setdefault(filename, PilotSkin.from_filename(filename))
                    except TypeError:
                        filename = elem.strip()
                        skins.setdefault(filename, PilotSkin.from_filename(filename))
                    else:
                        for tab in tabber:
                            if isinstance(tab, dict):
                                filename = tab["file"]
                                skins.setdefault(filename, PilotSkin.from_filename(filename))

                    for elem in basic_info.get("skins", []):
                        if isinstance(elem, dict):
                            if "skin_gallery" in elem:
                                skin_galleries.append(elem)

                if "skin_gallery" in item:
                    skin_galleries.append(item)

                for sg in skin_galleries:
                    for s in sg["skin_gallery"]:
                        filename, _, name = s.partition("|")
                        if filename.startswith("File:"):
                            filename = filename[5:]
                        skins.setdefault(filename, PilotSkin.from_filename(filename))

        pilot = Pilot(
            index = page_id,
            en_name = basic_info["name (english/romaji)"],
            jp_name = basic_info["name (original)"],
            page_name = raw["parse"]["title"],
            description = basic_info.get("background"),
            personality = basic_info["personality"],
            faction = basic_info["affiliation"],
            artist = basic_info.get("artist"),
            voice_actor = basic_info.get("seiyuu"),
            stats = PilotStats(
                melee = utils.to_int(basic_info["meleemax"]),
                ranged = utils.to_int(basic_info["shootingmax"]),
                defense = utils.to_int(basic_info["defensemax"]),
                reaction = utils.to_int(basic_info["reactionmax"])
            ),
            skills = (
                PilotSkill(
                    name = basic_info["activeskillname"],
                    effect = basic_info["activeskilleffect"],
                    copilot = COPILOT_SLOTS.get(basic_info.get("activeskilltype", "").lower())
                ),
                PilotSkill(
                    name = basic_info["passiveskill1name"],
                    effect = basic_info["passiveskill1effect"],
                    copilot = COPILOT_SLOTS.get(basic_info.get("passiveskill1type", "").lower())
                ),
                PilotSkill(
                    name = basic_info["passiveskill2name"],
                    effect = basic_info["passiveskill2effect"],
                    copilot = COPILOT_SLOTS.get(basic_info.get("passiveskill2type", "").lower())
                ),
                PilotSkill(
                    name = basic_info["passiveskill3name"],
                    effect = basic_info["passiveskill3effect"],
                    copilot = COPILOT_SLOTS.get(basic_info.get("passiveskill3type", "").lower())
                )
            ),
            copilot_slots = PilotCopilotSlots(
                Attack = bool(basic_info.get("copilotattack")),
                Tech = bool(basic_info.get("copilottech")),
                Defense = bool(basic_info.get("copilotdefense")),
                Support = bool(basic_info.get("copilotsupport")),
                Control = bool(basic_info.get("copilotcontrol")),
                Special = bool(basic_info.get("copilotspecial"))
            ),
            skins = list(skins.values())
        )

        print(pilot)

        return pilot

    @update.command(name = "part")
    @ac.check(checks.owner_only())
    async def update_part(self, interaction: Interaction, message_id: str):
        try:
            message_id = int(message_id)
            message = await interaction.channel.fetch_message(message_id)
            attachment = message.attachments[0]
        except (ValueError, IndexError):
            return await interaction.response.send_message("Invalid file.")

        bytes_ = await attachment.read()
        data = json.loads(bytes_)
        col = self.bot.mongo.db.iron_saga_parts
        await col.delete_many({})
        for index, doc in enumerate(data):
            await col.insert_one(doc)
        await interaction.response.send_message("Done.")

    @update.command(name = "pet")
    @ac.check(checks.owner_only())
    async def update_pet(self, interaction: Interaction, message_id: str):
        try:
            message_id = int(message_id)
            message = await interaction.channel.fetch_message(message_id)
            attachment = message.attachments[0]
        except (ValueError, IndexError):
            return await interaction.response.send_message("Invalid file.")

        bytes_ = await attachment.read()
        data = json.loads(bytes_)
        col = self.bot.mongo.db.iron_saga_pets
        await col.delete_many({})
        for index, doc in enumerate(data):
            await col.insert_one(doc)
        await interaction.response.send_message("Done.")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(IronSaga(bot))
