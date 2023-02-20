from discord import ui
import typing
import abc

from belphegor import utils
from . import text_inputs
from .metas import PostInitable
from ..discord_types import Interaction

#=============================================================================================================================#

class Modal(PostInitable, ui.Modal):
    @abc.abstractmethod
    async def on_submit(self, interaction: Interaction):
        pass

    async def on_timeout(self):
        self.stop()

class InputModal(Modal):
    title: str = "Input"

    input_text_box: text_inputs.InputTextBox

    def create_text_box(self) -> text_inputs.InputTextBox:
        text_box = utils.get_default_attribute(self, "input_text_box")
        return text_box

    def __post_init__(self):
        self.input_text_box = self.create_text_box()
        self.add_item(self.input_text_box)

class JumpToModal(InputModal):
    title: str = "Jump"

    input_text_box: text_inputs.JumpToTextBox

    @abc.abstractmethod
    async def on_submit(self, interaction: Interaction):
        return self.input_text_box.int_value
