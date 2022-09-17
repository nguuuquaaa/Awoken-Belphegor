from discord import ui

from belphegor import utils
from .metas import PostInitable

#=============================================================================================================================#

class Modal(PostInitable, ui.Modal):
    @utils.copy_signature(ui.Modal.__init__)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
