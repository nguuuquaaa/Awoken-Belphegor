import discord
from discord import app_commands as ac, ui
from typing import Any, Generic, TypeVar, overload, Literal, ForwardRef
from typing_extensions import Self
from collections.abc import Callable, AsyncGenerator
import asyncio
from pydantic.generics import GenericModel

from belphegor import utils
from belphegor.ext_types import Interaction, View, Item
from .views import StandardView
from .buttons import NextButton, PreviousButton, JumpForwardButton, JumpBackwardButton, JumpToButton
from .selects import BaseSelect

#=============================================================================================================================#

_VT = TypeVar("_VT")
_PageItem_VT = ForwardRef("PageItem[_VT]")

#=============================================================================================================================#

class EmbedTemplate(GenericModel, Generic[_VT]):
    title: str = None
    url: str = None
    colour: discord.Colour = None
    author: tuple[str, str | None, str | None] = None
    thumbnail_url: str = None
    image_url: str = None
    footer: tuple[str, str | None] = None
    description: str | Callable[[_PageItem_VT, int], str] = None
    fields: Callable[[_PageItem_VT, int], tuple[str, str, bool]] = None

    separator: str = "\n"

    class Config:
        arbitrary_types_allowed = True

    @overload
    def _get_value(self, key: Literal["colour"]) -> discord.Colour | None:
        pass

    @overload
    def _get_value(self, key: Literal["footer"]) -> tuple[str, str | None] | None:
        pass

    @overload
    def _get_value(self, key: Literal["author"]) -> tuple[str, str | None, str | None] | None:
        pass

    @overload
    def _get_value(self, key: Literal["description"], item: _PageItem_VT , index: int) -> str | None:
        pass

    @overload
    def _get_value(self, key: Literal["fields"], item: _PageItem_VT , index: int) -> tuple[str, str, bool] | None:
        pass

    @overload
    def _get_value(self, key: Literal["title", "url", "thumbnail_url", "image_url"]) -> str | None:
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

class PageItem(GenericModel, Generic[_VT]):
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

class SingleRowPaginator(Generic[_VT]):
    queue: asyncio.Queue[tuple[Interaction, _VT]]
    items: list[PageItem[_VT]]
    page_size: int
    pages: list[tuple[PageItem[_VT], ...]]
    page_amount: int
    current_index: int

    class PaginatorView(StandardView):
        paginator: "SingleRowPaginator[_VT]"

        class _HasPaginatorMixin:
            paginator: "SingleRowPaginator[_VT]"

        class PaginatorNextButton(NextButton["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            async def callback(self, interaction: Interaction):
                paginator = self.paginator
                paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + 1)
                embed, view = paginator.render(allowed_user = interaction.user, timeout = self.view.timeout)
                await interaction.response.edit_message(embed = embed, view = view)

        class PaginatorPreviousButton(PreviousButton["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            async def callback(self, interaction: Interaction):
                paginator = self.paginator
                paginator.current_index = max(0, paginator.current_index - 1)
                embed, view = paginator.render(allowed_user = interaction.user, timeout = self.view.timeout)
                await interaction.response.edit_message(embed = embed, view = view)

        class PaginatorJumpForwardButton(JumpForwardButton["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            async def callback(self, interaction: Interaction):
                paginator = self.paginator
                paginator.current_index = min(paginator.page_amount - 1, paginator.current_index + self.jump)
                embed, view = paginator.render(allowed_user = interaction.user, timeout = self.view.timeout)
                await interaction.response.edit_message(embed = embed, view = view)

        class PaginatorJumpBackwardButton(JumpBackwardButton["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            async def callback(self, interaction: Interaction):
                paginator = self.paginator
                paginator.current_index = max(0, paginator.current_index - self.jump)
                embed, view = paginator.render(allowed_user = interaction.user, timeout = self.view.timeout)
                await interaction.response.edit_message(embed = embed, view = view)

        class PaginatorJumpToButton(JumpToButton["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            async def callback(self, interaction: Interaction):
                paginator = self.paginator
                asyncio.create_task(interaction.response.send_modal(self.create_modal()))
                try:
                    interaction, text_input = await asyncio.wait_for(self.queue.get(), timeout = self.view.timeout)
                except asyncio.TimeoutError:
                    return

                try:
                    target_index = text_input.int_value - 1
                except ValueError:
                    await interaction.response.defer()
                else:
                    paginator.current_index = min(max(0, target_index), paginator.page_amount - 1)
                    embed, view = paginator.render(allowed_user = interaction.user, timeout = self.view.timeout)
                    await interaction.response.edit_message(embed = embed, view = view)

        class PaginatorSelect(BaseSelect["SingleRowPaginator.PaginatorView"], _HasPaginatorMixin):
            placeholder = "Select"
            min_values = 1
            max_values = 1

            async def callback(self, interaction: Interaction):
                values = self.values
                await self.paginator.queue.put((interaction, values[0]))

            def add_items_as_options(self, items: list[PageItem[_VT]], current_index: int):
                for i, item in enumerate(items):
                    self.add_option(
                        label = f"{i + current_index + 1}. {item.value}",
                        value = item.value
                    )

        def add_item(self, item: Item) -> Self:
            item.paginator = self.paginator
            super().add_item(item)
            return self

    class PaginatorTemplate(EmbedTemplate[_VT]):
        pass

    def __init__(self, items: PageItem[_VT] | list[PageItem[_VT]], *, page_size = 20):
        if isinstance(items, PageItem):
            self.items = items.children
        else:
            self.items = items

        self.page_size = page_size
        self.pages = list(utils.grouper(self.items, page_size, incomplete = "missing"))
        self.page_amount = len(self.pages)
        self.current_index = 0
        self.queue = asyncio.Queue()

    def render(self, *, allowed_user: discord.User, timeout: int | float = 180.0) -> tuple[discord.Embed, View]:
        current_items = self.pages[self.current_index]
        current_first_index = self.page_size * self.current_index

        template = self.PaginatorTemplate()
        if template.description is None:
            template.description = lambda item, index: f"{index + 1}. {item.value}"
        embed = template(current_items, current_first_index)

        view = self.PaginatorView(allowed_user = allowed_user, timeout = timeout)
        view.paginator = self

        next_button = self.PaginatorView.PaginatorNextButton(row = 1)
        previous_button = self.PaginatorView.PaginatorPreviousButton(row = 1)
        jump_forward_button = self.PaginatorView.PaginatorJumpForwardButton(row = 1)
        jump_backward_button = self.PaginatorView.PaginatorJumpBackwardButton(row = 1)
        jump_to_button = self.PaginatorView.PaginatorJumpToButton(label = f"Page {self.current_index + 1} of {self.page_amount}", row = 1)

        select = self.PaginatorView.PaginatorSelect(row = 0)
        select.add_items_as_options(current_items, current_first_index)

        view.add_item(select)
        view.add_item(jump_backward_button)
        view.add_item(previous_button)
        view.add_item(jump_to_button)
        view.add_item(next_button)
        view.add_item(jump_forward_button)

        return embed, view

    async def setup(self, interaction: Interaction, *, timeout: int | float = 180.0) -> AsyncGenerator[tuple[Interaction, _VT]]:
        embed, view = self.render(allowed_user = interaction.user, timeout = timeout)
        asyncio.create_task(interaction.response.send_message(embed = embed, view = view))
        while True:
            try:
                interaction, value = await asyncio.wait_for(self.queue.get(), timeout = view.timeout)
            except asyncio.TimeoutError:
                return
            else:
                yield interaction, value
