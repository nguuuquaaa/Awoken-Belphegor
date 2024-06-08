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
from belphegor.templates import ui_ex, paginators
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
        super().__init__()
        self.parser = calculator.MathParse()

#=============================================================================================================================#

class SaucenaoConfirmed(paginators.ConfirmedButton):
    paginator: "SaucenaoHiddenResults"

    async def callback(self, interaction: Interaction):
        self.paginator.edit_blueprint(embed = self.paginator.hidden_results)
        await self.paginator.update()

class SaucenaoDenied(paginators.DeniedButton):
    paginator: "SaucenaoHiddenResults"

    async def callback(self, interaction: Interaction):
        self.view.stop()
        await interaction.response.edit_message(view = None)

class SaucenaoHiddenResults(paginators.YesNoPrompt):
    hidden_results: discord.Embed

    def __init__(self, hidden_results: discord.Embed):
        self.hidden_results = hidden_results

    def render(self):
        super().render()
        self.edit_blueprint(content = "No result found.\nDo you want to see low similarity results?")

#=============================================================================================================================#

class Misc(commands.Cog):
    def __init__(self, bot: "Belphegor"):
        self.bot = bot

    async def cog_unload(self):
        await asyncio.get_running_loop().run_in_executor(self.pool.shutdown(wait = True, cancel_futures = False))

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

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Misc(bot))
