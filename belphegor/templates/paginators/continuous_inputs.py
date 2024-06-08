from belphegor.templates import ui_ex
from belphegor.templates.discord_types import Interaction
from .base import BasePaginator

#=============================================================================================================================#

class ContinuousInputModal(ui_ex.InputModal):
    paginator: "ContinuousInput"

    input_text_box: ui_ex.InputTextBox

class ContinuousInputButton(ui_ex.InputButton):
    paginator: "ContinuousInput"

    input_modal: ContinuousInputModal

    def create_modal(self) -> ContinuousInputModal:
        modal = super().create_modal()
        modal.paginator = self.paginator
        return modal

class ContinuousInput(BasePaginator):
    continuous_input_button: ContinuousInputButton

    def render(self):
        if not self.view:
            view = self.view = ui_ex.View()
            self.continuous_input_button = self.get_paginator_attribute("continuous_input_button")
            view.add_item(self.continuous_input_button)
            view.add_exit_button()

        return self

    async def initialize(self, interaction: Interaction):
        self.render()
        self.view.allowed_user = interaction.user
        await self.continuous_input_button.callback(interaction)
