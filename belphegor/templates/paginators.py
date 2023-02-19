import discord
import typing
from typing_extensions import Self
from collections.abc import Callable
import asyncio
from pydantic.generics import GenericModel
import abc

from belphegor import utils
from . import ui_ex
from .panels import Panel

if typing.TYPE_CHECKING:
    from .discord_types import Interaction

#=============================================================================================================================#

log = utils.get_logger()

#=============================================================================================================================#

_VT = typing.TypeVar("_VT")
_PageItem_VT = typing.ForwardRef("PageItem[_VT]")

class EmbedTemplate(GenericModel, typing.Generic[_VT]):
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

EmbedTemplate.update_forward_refs()

#=============================================================================================================================#

class PageItem(GenericModel, typing.Generic[_VT]):
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

PageItem.update_forward_refs()

#=============================================================================================================================#

class BasePaginator(ui_ex.PostInitable):
    panel: Panel

    class PaginatorView(ui_ex.StandardView):
        paginator: "BasePaginator"

    def __post_init__(self):
        self.panel = Panel()

    async def update(self, interaction: Interaction):
        await self.panel.reply(interaction)

    @abc.abstractmethod
    def render(self) -> Panel:
        return self.panel

    async def initialize(self, interaction: Interaction):
        self.render()
        self.panel.view.allowed_user = interaction.user
        await self.update(interaction)

#=============================================================================================================================#

_SRP = typing.TypeVar("_SRP", bound = "SingleRowPaginator")
_SRPV = typing.TypeVar("_SRPV", bound = "SingleRowPaginator.PaginatorView")

class SingleRowPaginator(BasePaginator, typing.Generic[_VT]):
    items: list[PageItem[_VT]]
    page_size: int
    pages: list[tuple[PageItem[_VT], ...]]
    page_amount: int
    current_index: int
    selectable: bool

    class PaginatorView(BasePaginator.PaginatorView):
        paginator: _SRP

    class PaginatorNextButton(ui_ex.NextButton[_SRPV]):
        async def callback(self, interaction: Interaction):
            paginator = self.view.paginator
            paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + 1)
            paginator.render()
            await paginator.update(interaction)

    class PaginatorPreviousButton(ui_ex.PreviousButton[_SRPV]):
        async def callback(self, interaction: Interaction):
            paginator = self.view.paginator
            paginator.current_index = max(0, paginator.current_index - 1)
            paginator.render()
            await paginator.update(interaction)

    class PaginatorJumpForwardButton(ui_ex.JumpForwardButton[_SRPV]):
        async def callback(self, interaction: Interaction):
            paginator = self.view.paginator
            paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + self.jump)
            paginator.render()
            await paginator.update(interaction)

    class PaginatorJumpBackwardButton(ui_ex.JumpBackwardButton[_SRPV]):
        async def callback(self, interaction: Interaction):
            paginator = self.view.paginator
            paginator.current_index = max(0, paginator.current_index - self.jump)
            paginator.render()
            await paginator.update(interaction)

    class PaginatorJumpToButton(ui_ex.JumpToButton[_SRPV]):
        class PaginatorModal(ui_ex.JumpToButton.InputModal):
            view: _SRPV

            async def on_submit(self, interaction: Interaction):
                paginator = self.view.paginator
                try:
                    target_index = self.input_text_box.int_value - 1
                except ValueError:
                    await paginator.panel.defer()
                else:
                    paginator.current_index = min(max(0, target_index), paginator.page_amount - 1)
                    paginator.render()
                    await paginator.update(interaction)

    class PaginatorSelect(ui_ex.Select[_SRPV]):
        placeholder: str = "Select"
        min_values: int = 1
        max_values: int = 1

        @abc.abstractmethod
        async def callback(self, interaction: Interaction):
            return self.values[0]

        def add_items_as_options(self, items: list[PageItem[_VT]], current_index: int):
            for i, item in enumerate(items):
                self.add_option(
                    label = f"{i + current_index + 1}. {item.value}",
                    value = item.value
                )

    class PaginatorTemplate(EmbedTemplate[_VT]):
        pass

    def __init__(self, items: PageItem[_VT] | list[PageItem[_VT]] | list[_VT], *, page_size = 20, selectable = False):
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

    _jump_to_button: PaginatorJumpToButton
    _select: PaginatorSelect

    def render(self) -> Panel:
        current_items = self.pages[self.current_index]
        current_first_index = self.page_size * self.current_index

        template = self.PaginatorTemplate()
        if template.description is None and template.fields is None:
            template.description = lambda item, index: f"{index + 1}. {item.value}"
        embed = template(current_items, current_first_index)
        self.panel.embed = embed

        if self.panel.view:
            self._jump_to_button.label = f"Page {self.current_index + 1} of {self.page_amount}"
            if self.selectable:
                self._select.options = []
                self._select.add_items_as_options(current_items, current_first_index)
        else:
            view = self.PaginatorView()
            view.paginator = self

            view.add_item(self.PaginatorJumpBackwardButton(row = 1))
            view.add_item(self.PaginatorPreviousButton(row = 1))
            self._jump_to_button = self.PaginatorJumpToButton(label = f"Page {self.current_index + 1} of {self.page_amount}", row = 1)
            view.add_item(self._jump_to_button)
            view.add_item(self.PaginatorNextButton(row = 1))
            view.add_item(self.PaginatorJumpForwardButton(row = 1))

            if self.selectable:
                self._select = self.PaginatorSelect(row = 0)
                self._select.add_items_as_options(current_items, current_first_index)
                view.add_item(self._select)

            view.add_exit_button(row = 2)

            self.panel.view = view

        return self.panel

#=============================================================================================================================#

_CI = typing.TypeVar("_CI", bound = "ContinuousInput")
_CIV = typing.TypeVar("_CIV", bound = "ContinuousInput.PaginatorView")

class ContinuousInput(BasePaginator):
    class PaginatorView(BasePaginator.PaginatorView):
        paginator: _CI

    class ContinuousInputButton(ui_ex.InputButton[_CIV]):
        class ContinuousInputModal(ui_ex.InputButton.InputModal):
            pass

    def render(self):
        if not self.panel.view:
            view = self.PaginatorView()
            view.add_item(self.ContinuousInputButton())
            view.add_exit_button()
            self.panel.view = view

    async def initialize(self, interaction: Interaction):
        self.render()
        self.panel.view.allowed_user = interaction.user
        await interaction.response.send_modal(self.ContinuousInputButton().create_modal())
