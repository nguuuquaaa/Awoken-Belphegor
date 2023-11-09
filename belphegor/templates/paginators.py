import discord
import typing
from collections.abc import Callable
import asyncio
from pydantic import BaseModel
import abc

from belphegor import utils
from . import ui_ex
from .panels import Panel
from .discord_types import Interaction

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

_V = typing.TypeVar("_V", bound = ui_ex.StandardView)
_VT = typing.TypeVar("_VT")
_PageItem_VT = typing.ForwardRef("PageItem[_VT]")

class PageItem(BaseModel, typing.Generic[_VT]):
    value: _VT
    children: list[_PageItem_VT] = []

    class Config:
        arbitrary_types_allowed = True

    def __getitem__(self, key: int | tuple[int]) -> _PageItem_VT:
        if isinstance(key, int):
            return self.children[key]
        else:
            if len(key) == 0:
                return self
            else:
                return self.children[key[0]][key[1:]]

PageItem.model_rebuild()

#=============================================================================================================================#

class EmbedTemplate(BaseModel, typing.Generic[_VT]):
    title: str | None = None
    url: str | None = None
    colour: discord.Colour | None = None
    author: tuple[str, str | None, str | None] | None = None
    thumbnail_url: str | None = None
    image_url: str | None = None
    footer: tuple[str, str | None] | None = None
    description: str | Callable[[_PageItem_VT, int], str] | None = None
    fields: tuple[str, str, bool] | Callable[[_PageItem_VT, int], tuple[str, str, bool]] | None = None

    separator: str = "\n"

    class Config:
        arbitrary_types_allowed = True

    @typing.overload
    def _get_value(self, key: typing.Literal["colour"]) -> discord.Colour | None:
        pass

    @typing.overload
    def _get_value(self, key: typing.Literal["footer"]) -> tuple[str, str | None] | None:
        pass

    @typing.overload
    def _get_value(self, key: typing.Literal["author"]) -> tuple[str, str | None, str | None] | None:
        pass

    @typing.overload
    def _get_value(self, key: typing.Literal["description"], item: _PageItem_VT , index: int) -> str | None:
        pass

    @typing.overload
    def _get_value(self, key: typing.Literal["fields"], item: _PageItem_VT , index: int) -> tuple[str, str, bool] | None:
        pass

    @typing.overload
    def _get_value(self, key: typing.Literal["title", "url", "thumbnail_url", "image_url"]) -> str | None:
        pass

    def _get_value(self, key: str, item: _PageItem_VT = None, index: int = 0) -> str | discord.Colour | tuple | None:
        v = getattr(self, key)
        if callable(v):
            return v(item, index)
        else:
            return v

    def __call__(self, items: list[_PageItem_VT], first_index: int) -> discord.Embed:
        embed = discord.Embed(
            title = self._get_value("title"),
            url = self._get_value("url"),
            colour = self._get_value("colour")
        )

        desc_list = []
        for i, item in enumerate(items):
            desc = self._get_value("description", item, first_index + i)
            if desc:
                desc_list.append(desc)
            field = self._get_value("fields", item, first_index + i)
            if field:
                name, value, inline = field
                if name and value:
                    embed.add_field(name = name, value = value, inline = inline)
        if desc_list:
            description = self.separator.join(desc_list)
            embed.description = description

        embed.set_thumbnail(url = self._get_value("thumbnail_url"))
        embed.set_image(url = self._get_value("image_url"))

        author = self._get_value("author")
        if author:
            name, url, icon = author
            embed.set_author(name = name, url = url, icon_url = icon)

        footer = self._get_value("footer")
        if footer:
            text, icon = footer
            embed.set_footer(text = text, icon_url = icon)

        return embed

EmbedTemplate.model_rebuild()

#=============================================================================================================================#

class BasePaginator:
    panel: Panel

    def __init__(self):
        self.panel = Panel()

    @abc.abstractmethod
    def render(self) -> Panel:
        return self.panel

    async def update(self, interaction: Interaction):
        self.render()
        await self.panel.reply(interaction)

    async def initialize(self, interaction: Interaction):
        self.render()
        self.panel.view.allowed_user = interaction.user
        await self.panel.reply(interaction)

    def get_paginator_attribute(self, key: str, *args, **kwargs):
        value = utils.get_default_attribute(self, key, *args, **kwargs)
        hints = typing.get_type_hints(type(value))
        if "paginator" in hints:
            value.paginator = self
        return value

#=============================================================================================================================#

class PaginatorNextButton(ui_ex.NextButton[_V]):
    paginator: "SingleRowPaginator"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + 1)
        await paginator.update(interaction)

class PaginatorPreviousButton(ui_ex.PreviousButton[_V]):
    paginator: "SingleRowPaginator"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.current_index = max(0, paginator.current_index - 1)
        await paginator.update(interaction)

class PaginatorJumpForwardButton(ui_ex.JumpForwardButton[_V]):
    paginator: "SingleRowPaginator"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + self.jump)
        await paginator.update(interaction)

class PaginatorJumpBackwardButton(ui_ex.JumpBackwardButton[_V]):
    paginator: "SingleRowPaginator"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        paginator.current_index = max(0, paginator.current_index - self.jump)
        await paginator.update(interaction)

class PaginatorJumpToModal(ui_ex.JumpToModal):
    paginator: "SingleRowPaginator"

    async def on_submit(self, interaction: Interaction):
        paginator = self.paginator
        try:
            target_index = self.input_text_box.int_value - 1
        except ValueError:
            await paginator.panel.defer()
        else:
            paginator.current_index = min(max(0, target_index), paginator.page_amount - 1)
            await paginator.update(interaction)

class PaginatorJumpToButton(ui_ex.JumpToButton[_V]):
    paginator: "SingleRowPaginator"

    input_modal: PaginatorJumpToModal

    def create_modal(self) -> PaginatorJumpToModal:
        modal = super().create_modal()
        modal.paginator = self.paginator
        return modal

class PaginatorSelect(ui_ex.SelectOne[_V]):
    paginator: "SingleRowPaginator"

    def add_items_as_options(self, items: list[PageItem[_VT]], current_index: int):
        for i, item in enumerate(items):
            self.add_option(
                label = f"{i + current_index + 1}. {item.value}",
                value = item.value
            )

class PaginatorEmbedTemplate(EmbedTemplate[_VT]):
    colour: discord.Colour = discord.Colour.blue()
    description: Callable[[PageItem[_VT], int], str] = lambda item, index: f"{index + 1}. {item.value}"

class SingleRowPaginator(BasePaginator, typing.Generic[_VT]):
    items: list[PageItem[_VT]]
    page_size: int
    pages: list[tuple[PageItem[_VT], ...]]
    page_amount: int
    current_index: int
    selectable: bool

    next_button: PaginatorNextButton
    previous_button: PaginatorPreviousButton
    jump_forward_button: PaginatorJumpForwardButton
    jump_backward_button: PaginatorJumpBackwardButton
    jump_to_button: PaginatorJumpToButton
    select_menu: PaginatorSelect
    embed_template: PaginatorEmbedTemplate

    def __init__(self, items: PageItem[_VT] | list[PageItem[_VT]] | list[_VT], *, page_size: int = 20, selectable: bool = False):
        super().__init__()
        if isinstance(items, PageItem):
            self.items = items.children
        else:
            self.items = [item if isinstance(item, PageItem) else PageItem(value = item) for item in items]

        self.page_size = page_size
        self.pages = list(utils.grouper(self.items, page_size, incomplete = "missing"))
        self.page_amount = len(self.pages)
        self.current_index = 0
        self.queue = asyncio.Queue()
        self.selectable = selectable

    def create_embed(self) -> discord.Embed:
        current_items = self.pages[self.current_index]
        current_first_index = self.page_size * self.current_index

        template = self.get_paginator_attribute("embed_template")
        embed = template(current_items, current_first_index)
        self.panel.embed = embed

        return embed

    def create_view(self) -> ui_ex.StandardView:
        current_items = self.pages[self.current_index]
        current_first_index = self.page_size * self.current_index

        if self.panel.view:
            self.jump_to_button.label = f"Page {self.current_index + 1} of {self.page_amount}"
            if self.selectable:
                self.select_menu.options = []
                self.select_menu.add_items_as_options(current_items, current_first_index)
        else:
            view = ui_ex.StandardView()

            view.add_item(self.get_paginator_attribute("jump_backward_button", row = 1))
            view.add_item(self.get_paginator_attribute("previous_button", row = 1))
            self.jump_to_button = self.get_paginator_attribute("jump_to_button", label = f"Page {self.current_index + 1} of {self.page_amount}", row = 1)
            view.add_item(self.jump_to_button)
            view.add_item(self.get_paginator_attribute("next_button", row = 1))
            view.add_item(self.get_paginator_attribute("jump_forward_button", row = 1))

            if self.selectable:
                self.select_menu = self.get_paginator_attribute("select_menu", row = 0)
                self.select_menu.add_items_as_options(current_items, current_first_index)
                view.add_item(self.select_menu)

            view.add_exit_button(row = 2)

            self.panel.view = view

        return self.panel.view

    def render(self) -> Panel:
        self.create_embed()
        self.create_view()
        return self.panel

#=============================================================================================================================#

class ContinuousInputButton(ui_ex.InputButton):
    paginator: "ContinuousInput"

class ContinuousInput(BasePaginator):
    continuous_input_button: ContinuousInputButton

    def render(self) -> Panel:
        if not self.panel.view:
            view = ui_ex.StandardView()
            self.continuous_input_button = self.get_paginator_attribute("continuous_input_button")
            view.add_item(self.continuous_input_button)
            view.add_exit_button()
            self.panel.view = view
        return self.panel

    async def initialize(self, interaction: Interaction):
        self.render()
        self.panel.view.allowed_user = interaction.user
        await self.continuous_input_button.callback(interaction)
