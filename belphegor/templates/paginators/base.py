import typing

from belphegor import utils
from belphegor.templates.panels import ControlPanel
from belphegor.templates.discord_types import Interaction

#=============================================================================================================================#

class BasePaginator(ControlPanel):
    def render(self):
        return self

    async def initialize(self, interaction: Interaction, *, public: bool = False):
        self.render()
        if not public:
            self.view.allowed_user = interaction.user
        await self.reply(interaction)

    async def update(self, interaction: Interaction):
        self.render()
        await self.reply(interaction)

    def get_paginator_attribute(self, key: str, *args, **kwargs):
        value = utils.get_default_attribute(self, key, *args, **kwargs)
        hints = typing.get_type_hints(type(value))
        if "paginator" in hints:
            value.paginator = self
        return value
