import discord
from discord import app_commands as ac, ui
from discord.ext import commands
from pydantic import BaseModel
from typing import Literal
from collections.abc import Callable
from urllib.parse import quote
import re
from functools import partial

from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction, View
from belphegor.templates.views import StandardView
from belphegor.templates.buttons import BaseButton, TriviaButton, SkinsButton
from belphegor.templates.selects import BaseSelect
from belphegor.templates.paginators import SingleRowPaginator, PageItem
from belphegor.utils import CircleIter, grouper

#==================================================================================================================================================

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

class PilotStats(BaseModel):
    melee: int
    ranged: int
    defense: int
    reaction: int

class PilotSkill(BaseModel):
    name: str
    effect: str
    copilot: str | None

class PilotSkin(BaseModel):
    name: str
    url: str

class PilotCopilotSlots(BaseModel):
    Attack: bool
    Tech: bool
    Defense: bool
    Support: bool
    Control: bool
    Special: bool

class Pilot(BaseModel):
    index: int
    en_name: str
    jp_name: str
    page_name: str
    faction: str
    stats: PilotStats
    personality: Literal["Brave", "Calm", "Energetic", "Extreme", "Friendly", "Gentle", "Impatient", "Lazy", "Mighty", "Normal", "Peaceful", "Rational", "Sensitive", "Timid"]
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

class IronSaga(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

    @ac.command(name = "pilot")
    @ac.describe(name = "Pilot name")
    async def get_pilot(
        self,
        interaction: Interaction,
        name: str
    ):
        pilots: dict[str, Pilot] = {}
        async for doc in self.bot.db.pilot_index.aggregate([
            {
                "$match": {
                    "$or": [
                        {
                            "en_name": {
                                "$regex": ".*?".join(map(re.escape, name.split())),
                                "$options": "i"
                            }
                        },
                        {
                            "aliases": {
                                "$regex": ".*?".join(map(re.escape, name.split())),
                                "$options": "i"
                            }
                        }
                    ]
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
            return await interaction.response.send_message(f"Can't find any pilot with name {name}")

        if len(pilots) > 1:
            class PilotPaginator(SingleRowPaginator):
                class PaginatorView(SingleRowPaginator.PaginatorView):
                    class PaginatorSelect(SingleRowPaginator.PaginatorView.PaginatorSelect):
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
            await interaction.response.edit_message(embed = view.embed_display(), view = view)
        else:
            pilot = list(pilots.values())[0]
            del pilots
            view = PilotView.from_pilot(pilot)
            await interaction.response.send_message(embed = view.embed_display(), view = view)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(IronSaga(bot))
