import discord
from discord import app_commands as ac, ui
from discord.ext import commands
from pydantic import BaseModel, Field
from typing import Literal, TypeAlias, Optional
from collections.abc import Callable
from urllib.parse import quote
import json
from functools import partial
import time
import traceback

from belphegor import errors, utils
from belphegor.utils import CircleIter, grouper, wiki
from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction, File
from belphegor.templates.views import StandardView
from belphegor.templates.buttons import BaseButton, TriviaButton, SkinsButton
from belphegor.templates.selects import BaseSelect
from belphegor.templates.paginators import SingleRowPaginator, PageItem
from belphegor.templates.checks import Check

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

PilotPersonality: TypeAlias = Literal["Brave", "Calm", "Energetic", "Extreme", "Friendly", "Gentle", "Impatient", "Lazy", "Mighty", "Normal", "Peaceful", "Rational", "Sensitive", "Timid"]

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

    def display_stats_info(self, view: "PilotView") -> discord.Embed:
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

        skin = view.skins.current().current()
        view.skin_select.placeholder = skin.name
        embed.set_image(url = skin.url)

        return embed

    def display_other_info(self, view: "PilotView") -> discord.Embed:
        embed = discord.Embed(
            title = self.en_name or self.page_name,
            description = self.description or "N/A",
            color = discord.Color.red(),
            url = f"{ISWIKI_BASE}/wiki/{quote(self.page_name)}"
        )
        embed.add_field(name = "Faction", value = self.faction, inline=False)
        embed.add_field(name = "Artist", value = self.artist or "N/A")
        embed.add_field(name = "Voice actor", value = self.voice_actor or "N/A")

        skin = view.skins.current().current()
        view.skin_select.placeholder = skin.name
        embed.set_image(url = skin.url)

        return embed

#=============================================================================================================================#

class ISStatsButton(BaseButton["PilotView"]):
    label = "Stats"
    emoji = discord.PartialEmoji(name = "exp_capsule", id = 824327490536341504)
    style = discord.ButtonStyle.primary

    async def callback(self, interaction: Interaction):
        view = self.view
        view.embed_display = partial(view.pilot.display_stats_info, view)
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class ISTriviaButton(TriviaButton["PilotView"]):
    async def callback(self, interaction: Interaction):
        view = self.view
        view.embed_display = partial(view.pilot.display_other_info, view)
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class ISSkinsButton(SkinsButton["PilotView"]):
    async def callback(self, interaction: Interaction):
        view = self.view
        view.show_next_skin_set()
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class ISSkinSelect(BaseSelect["PilotView"]):
    placeholder = "Select skin to display"
    min_values = 1
    max_values = 1

    async def callback(self, interaction: Interaction):
        view = self.view
        result = self.values[0]
        view.skins.current().jump_to(int(result))
        embed = view.embed_display()
        await interaction.response.edit_message(embed = embed, view = view)

class PilotView(StandardView):
    SKIN_SELECT_SIZE = 20

    pilot: Pilot
    skins: CircleIter[CircleIter[PilotSkin]]
    embed_display: Callable[[], discord.Embed]
    skin_select: ISSkinSelect

    @classmethod
    def from_pilot(cls, pilot: Pilot):
        view = cls()
        view.pilot = pilot
        view.skins = CircleIter([CircleIter(s, start_index = 0) for s in grouper(pilot.skins, cls.SKIN_SELECT_SIZE, incomplete = "missing")], start_index = -1)
        view.embed_display = partial(view.pilot.display_stats_info, view)
        view.show_next_skin_set()
        view.add_item(ISStatsButton(row = 1))
        view.add_item(ISTriviaButton(row = 1))
        view.add_item(ISSkinsButton(row = 1))
        view.add_exit_button(row = 1)
        return view

    def show_next_skin_set(self):
        if getattr(self, "skin_select", None):
            self.remove_item(self.skin_select)

        next(self.skins)
        set_index, batch = self.skins.current(True)
        batch.jump_to(0)
        skin_select = ISSkinSelect(row = 0)
        for i, skin in enumerate(batch.iter_once()):
            skin_select.add_option(
                label = f"{set_index * self.SKIN_SELECT_SIZE + i + 1}. {skin.name}",
                value = str(i)
            )
        self.skin_select = skin_select
        self.add_item(skin_select)

#=============================================================================================================================#

COLOR_MAPPING = {
    "S": discord.Color.purple(),
    "A": discord.Color.blue(),
    "B": discord.Color.green(),
    "C": discord.Color.light_grey()
}

class Part(BaseModel):
    name: str
    classification: Literal["core", "shell", "support", "armour", "coating"]
    rank: Literal["S", "A", "B", "C"]
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

class IronSaga(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @ac.command(name = "pilot")
    @ac.describe(name = "Pilot name")
    async def get_pilot(self, interaction: Interaction, name: str):
        pilots: dict[str, Pilot] = {}
        async for doc in self.bot.mongo.db.iron_saga_pilots.aggregate([
            {
                "$match": {
                    "$or": utils.QueryHelper.broad_search(name, ("en_name", "jp_name", "aliases"))
                }
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
            pilots[doc["en_name"]] = Pilot(**doc)

        if len(pilots) == 0:
            return await interaction.response.send_message(f"Can't find any pilot with name: {name}")

        if len(pilots) > 1:
            class PilotPaginator(SingleRowPaginator):
                class PaginatorSelect(SingleRowPaginator.PaginatorSelect):
                    placeholder = "Select pilot"

                class PaginatorTemplate(SingleRowPaginator.PaginatorTemplate):
                    title = f"Found {len(pilots)} pilots"
                    colour = discord.Colour.blue()

            items = [PageItem(value = pn) for pn in pilots]
            items.sort(key = lambda x: x.value)

            paginator = PilotPaginator(items = items, page_size = 20)
            async for interaction, value in paginator.setup(interaction, timeout = 180):
                break

            pilot = pilots[value]
            del pilots
            view = PilotView.from_pilot(pilot)
            view.allowed_user = interaction.user
            await interaction.response.edit_message(embed = view.embed_display(), view = view)
        else:
            pilot = list(pilots.values())[0]
            del pilots
            view = PilotView.from_pilot(pilot)
            view.allowed_user = interaction.user
            await interaction.response.send_message(embed = view.embed_display(), view = view)

    @ac.command(name = "part")
    @ac.describe(name = "Part name")
    async def get_part(self, interaction: Interaction, name: str):
        parts: dict[str, Part] = {}
        async for doc in self.bot.mongo.db.iron_saga_parts.aggregate([
            {
                "$match": {
                    "$or": utils.QueryHelper.broad_search(name, ("name", "aliases"))
                }
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
            parts[doc["name"]] = Part(**doc)

        if len(parts) == 0:
            return await interaction.response.send_message(f"Can't find any part with name: {name}")


        if len(parts) > 1:
            class PartPaginator(SingleRowPaginator):
                class PaginatorSelect(SingleRowPaginator.PaginatorSelect):
                    placeholder = "Select part"

                class PaginatorTemplate(SingleRowPaginator.PaginatorTemplate):
                    title = f"Found {len(parts)} parts"
                    colour = discord.Colour.blue()

            items = [PageItem(value = pn) for pn in parts]
            items.sort(key = lambda x: x.value)

            paginator = PartPaginator(items = items, page_size = 20)
            async for interaction, value in paginator.setup(interaction, timeout = 180):
                break

            part = parts[value]
            del parts
            await interaction.response.edit_message(embed = part.display())
        else:
            part = list(parts.values())[0]
            del parts
            await interaction.response.send_message(embed = part.display())

    @ac.command(name = "pet")
    @ac.describe(name = "Pet name")
    async def get_pet(self, interaction: Interaction, name: str):
        pets: dict[str, Pet] = {}
        async for doc in self.bot.mongo.db.iron_saga_pets.aggregate([
            {
                "$match": {
                    "$or": utils.QueryHelper.broad_search(name, ("name", "aliases"))
                }
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
            pets[doc["name"]] = Pet(**doc)

        if len(pets) == 0:
            return await interaction.response.send_message(f"Can't find any part with name: {name}")

        if len(pets) > 1:
            class PetPaginator(SingleRowPaginator):
                class PaginatorSelect(SingleRowPaginator.PaginatorSelect):
                    placeholder = "Select pet"

                class PaginatorTemplate(SingleRowPaginator.PaginatorTemplate):
                    title = f"Found {len(pets)} parts"
                    colour = discord.Colour.blue()

            items = [PageItem(value = pn) for pn in pets]
            items.sort(key = lambda x: x.value)

            paginator = PetPaginator(items = items, page_size = 20)
            async for interaction, value in paginator.setup(interaction, timeout = 180):
                break

            pet = pets[value]
            del pets
            await interaction.response.edit_message(embed = pet.display())
        else:
            pet = list(pets.values())[0]
            del pets
            await interaction.response.send_message(embed = pet.display())

    update = ac.Group(name = "update", description = "Update database")

    @update.command(name = "pilot")
    @ac.check(Check.owner_only())
    async def update_pilot(self, interaction: Interaction, name: Optional[str] = None):
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
    @ac.check(Check.owner_only())
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
    @ac.check(Check.owner_only())
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
