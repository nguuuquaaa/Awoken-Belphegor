import discord
from discord import app_commands as ac
from discord.ext import commands
import asyncio
import numpy as np
import time
from yarl import URL
import aiohttp
from bs4 import BeautifulSoup as BS
import typing

from belphegor import utils
from belphegor.settings import settings
from belphegor.templates import ui_ex, paginators, transformers
from belphegor.templates.discord_types import Interaction
from .misc_core import calculator

if typing.TYPE_CHECKING:
    from belphegor.bot import Belphegor

#=============================================================================================================================#

BOX_PATTERN = {
    (0, 0): " ",
    (0, 1): "\u2584",
    (1, 0): "\u2580",
    (1, 1): "\u2588"
}

#=============================================================================================================================#

class MathTextBox(ui_ex.InputTextBox):
    label: str = "Input formulas"
    min_length: int = 1
    max_length: int = 1000

class MathInputModal(paginators.ContinuousInputModal):
    paginator: "Calculator"

    input_text_box: MathTextBox

    async def on_submit(self, interaction: Interaction):
        paginator = self.paginator
        inp = self.input_text_box.value
        parser = self.paginator.parser

        await paginator.thinking(interaction)
        try:
            start = time.perf_counter()
            r = await asyncio.get_running_loop().run_in_executor(None, parser.result, inp)
            end = time.perf_counter()
            time_taken = end - start
        except calculator.ParseError as e:
            target = getattr(e, "target", parser)
            title = "Error"
            msg = f"{e}\n```\n{target.show_parse_error()}\n```"
        except ZeroDivisionError:
            title = "Error"
            msg = "Division by zero."
        except OverflowError:
            title = "Error"
            msg = "IO number too big. U sure need this one?"
        except ValueError as e:
            title = "Error"
            target = getattr(e, "target", parser)
            msg = f"Calculation error.\n```\n{target.show_parse_error()}\n```"
        except Exception as e:
            title = "Error"
            target = getattr(e, "target", parser)
            msg = f"Parsing error.\n```\n{target.show_parse_error()}\n```"
        else:
            title = f"Result in {1000*(time_taken):.2f}ms"
            r = "\n".join(r)
            msg = f"```\n{r}\n```"

        e = discord.Embed(title = title)
        e.add_field(name = "Input", value = f"```\n{inp}\n```", inline = False)
        e.add_field(name = "Result", value = msg, inline = False)

        paginator.edit_blueprint(embed = e)
        await paginator.reply(interaction)

class MathContinuousInputButton(paginators.ContinuousInputButton):
    paginator: "Calculator"

    input_modal: MathInputModal

class Calculator(paginators.ContinuousInput):
    parser: calculator.MathParse

    continuous_input_button: MathContinuousInputButton

    def __init__(self):
        self.parser = calculator.MathParse()

#=============================================================================================================================#

class SauceSelectMenu(paginators.PaginatorSelect):
    paginator: "SauceSelector"

    async def callback(self, interaction: Interaction):
        paginator = self.paginator
        url = paginator.images[self.values[0]]
        paginator.stop()
        paginator.view = None
        await paginator.request_sauce(interaction, url)

class SauceSelector(paginators.SingleRowPaginator):
    images: dict[str, str]

    select_menu: SauceSelectMenu

    @classmethod
    def from_images(cls, images: list[tuple[str, str]]):
        paginator = cls([paginators.PageItem(value = name) for name, url in images], selectable = True)
        paginator.images = {name: url for name, url in images}
        return paginator

    def render_embed(self):
        embed = super().render_embed()
        embed.title = f"Select image to search for sauce:"
        return embed

    async def request_sauce(self, interaction: Interaction, url: str):
        pass

#=============================================================================================================================#

class HiddenResultsConfirmed(paginators.ConfirmedButton):
    paginator: "SaucenaoHiddenResults"

    async def callback(self, interaction: Interaction):
        self.paginator.edit_blueprint(embed = self.paginator.hidden_results)
        await self.paginator.reply(interaction)

class HiddenResultsDenied(paginators.DeniedButton):
    paginator: "SaucenaoHiddenResults"

    async def callback(self, interaction: Interaction):
        self.view.shutdown()
        await self.paginator.reply(interaction)

class SaucenaoHiddenResults(paginators.YesNoPrompt):
    hidden_results: discord.Embed

    confirmed_button: HiddenResultsConfirmed
    denied_button: HiddenResultsDenied

    def __init__(self, hidden_results: discord.Embed):
        self.hidden_results = hidden_results
        self.edit_blueprint(content = "No result found.\nDo you want to see low similarity results?")

#=============================================================================================================================#

class Misc(commands.Cog):
    def __init__(self, bot: "Belphegor"):
        self.bot = bot

        self.saucenao_ctx_menu = ac.ContextMenu(
            name = 'Sauce?',
            callback = self.saucenao_context,
        )
        bot.tree.add_command(self.saucenao_ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.saucenao_ctx_menu.name, type = self.saucenao_ctx_menu.type)

    @ac.command(name = "eca")
    @ac.describe(rule_number = "Rule number")
    async def elementary_cellular_automaton(
        self,
        interaction: Interaction,
        rule_number: ac.Range[int, 1, 255]
    ):
        width = 64
        height = 60

        rule = np.array([(rule_number >> i) & 1 for i in range(8)], dtype = np.uint8).reshape((2, 2, 2))
        cells = np.random.randint(0, 2, size = (height, width), dtype = np.uint8)
        for x in range(height-1):
            for y in range(width):
                if y == 0:
                    left = 0
                    right = cells[x, y+1]
                elif y == width-1:
                    left = cells[x, y-1]
                    right = 0
                else:
                    left = cells[x, y-1]
                    right = cells[x, y+1]
                mid = cells[x, y]
                cells[x+1, y] = rule[left, mid, right]

        raw = []
        for x in range(0, height, 2):
            line = []
            for y in range(0, width):
                cut = cells[x:x+2, y:y+1]
                line.append(BOX_PATTERN[tuple(cut.flatten())])
            raw.append("".join(line))
        out = "\n".join(raw)

        await interaction.response.send_message(f"```\n{out}\n```")

    @ac.command(name = "calc", description = "A calculator with input rule be quite close to handwritten math formulas.")
    async def calc(
        self,
        interaction: Interaction
    ):
        '''
            Formulas are separated by linebreak. You can codeblock the whole thing for easier on the eyes.

            **Acceptable expressions:**
             - Operators `+` , `-` , `*` , `/` (true div), `//` (div mod), `%` (mod), `^`|`**` (pow), `!` (factorial)
             - Functions `sin`, `cos`, `tan`, `cot`, `arcsin`|`asin`, `arccos`|`acos`, `arctan`|`atan`, `log` (base 10), `ln` (natural log), `sqrt` (square root), `cbrt` (cube root), `root` (nth root), `abs` (absolute value), `nCk` (combination), `sign`|`sgn` (sign function), `gcd`|`gcf` (greatest common divisor/factor), `lcm` (least common multiple), `max`, `min`, `gamma`, `floor`, `ceil`, `round`
             - Constants `e`, `pi`|`π`, `tau`|`τ`, `i` (imaginary), `inf`|`∞` (infinity, use at your own risk)
             - Enclosed `()`, `[]`, `{}`, `\u2308 \u2309` (ceil), `\u230a \u230b` (floor)
             - Binary/octal/hexadecimal mode. Put `bin:`, `oct:`, `hex:` at the start to use that mode in current line. Default to decimal (`dec:`) mode (well of course)
             - Set a variable to a value (value can be a calculable formula) for next calculations
             - Define a function. User functions must be in `func_name(arg1, arg2...)` format, both at defining and using
             - Special function `sigma`|`Σ` (sum)
                Format: `sigma(n, from, to)(formula)`
                Due to how parser works, n must be a wildcard defined by `n = counter` prior to the sigma function.
             - Special function `reduce` (cumulate)
                Format: `reduce(function, n, from, to)(formula)`
                It's like sigma, but use `function` instead of sum.
                `function` can be either builtin or user-defined, but must take exactly 2 arguments.
             - Line that starts with `#` is comment
        '''

        calc = Calculator()
        await calc.initialize(interaction)

    async def request_sauce(self, interaction: Interaction, url: str):
        await interaction.response.defer(thinking = True)
        payload = aiohttp.FormData()
        payload.add_field("file", b"", filename = "", content_type = "application/octet-stream")
        payload.add_field("url", url)
        payload.add_field("frame", "1")
        payload.add_field("hide", "0")
        payload.add_field("database", "999")
        async with self.bot.session.post(
            "https://saucenao.com/search.php",
            headers = {
                "User-Agent": settings.USER_AGENT
            },
            data = payload
        ) as response:
            bytes_ = await response.read()
        data = BS(bytes_.decode("utf-8"), "lxml")
        results = []
        hidden_results = []
        for tag in data.find_all(lambda x: x.name == "div" and x.get("class") in [["result"], ["result", "hidden"]] and not x.get("id")):
            content = tag.find("td", class_ = "resulttablecontent")
            title_tag = content.find("div", class_ = "resulttitle")
            if title_tag:
                for br in title_tag.find_all("br"):
                    br.replace_with("\n")
                try:
                    title = title_tag.get_text().strip().splitlines()[0]
                except IndexError:
                    title = "no title"
            else:
                result_content = tag.find("div", class_ = "resultcontent")
                for br in result_content.find_all("br"):
                    br.replace_with("\n")
                title = utils.get_element(result_content.get_text().strip().splitlines(), 0, default = "No title")
            similarity = content.find("div", class_ = "resultsimilarityinfo").text
            content_url = content.find("a", class_ = "linkify")
            if not content_url:
                content_url = content.find("div", class_ = "resultmiscinfo").find("a")
            if content_url:
                # r = {"title": title, "similarity": similarity, "url": content_url["href"]}
                r = f"[{title} ({similarity})]({content_url['href']})"
            else:
                # r = {"title": title, "similarity": similarity, "url": ""}
                r = f"{title} ({similarity})"
            if "hidden" in tag["class"]:
                hidden_results.append(r)
            else:
                results.append(r)

        if results:
            embed = discord.Embed(
                title = "Sauce found?",
                description = "\n".join(results)
            )
            embed.set_footer(text = "Powered by https://saucenao.com")
            await interaction.followup.send(embed = embed)
        else:
            if hidden_results:
                embed = discord.Embed(
                    title = "Sauce found?",
                    description = "\n".join(hidden_results)
                )
                embed.set_footer(text = "Powered by https://saucenao.com")
                yes_no = SaucenaoHiddenResults(embed)
                await yes_no.initialize(interaction)
            else:
                await interaction.followup.send("No result found.")

    @ac.command(name = "saucenao", description = "Find the sauce of the image.")
    async def saucenao(
        self,
        interaction: Interaction,
        url: ac.Transform[URL, transformers.URLTransformer]
    ):
        await self.request_sauce(interaction, str(url))

    async def saucenao_context(self, interaction: Interaction, message: discord.Message):
        targets = []
        for i, attachment in enumerate(message.attachments):
            targets.append((f"Attachment {i + 1}", attachment.proxy_url))
        for i, embed in enumerate(message.embeds):
            if embed.image.proxy_url:
                targets.append((f"Image {i + 1}", embed.image.proxy_url))
            if embed.thumbnail.proxy_url:
                targets.append((f"Thumbnail {i + 1}", embed.thumbnail.proxy_url))

        if targets:
            if len(targets) > 1:
                sauce_selector = SauceSelector.from_images(targets)
                sauce_selector.request_sauce = self.request_sauce
                await sauce_selector.initialize(interaction)
            else:
                await self.request_sauce(interaction, targets[0][1])
        else:
            await interaction.response.send_message("This message doesn't have any attachment.")

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Misc(bot))
