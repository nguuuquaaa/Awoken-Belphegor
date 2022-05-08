import discord
from discord import app_commands as ac
from discord.enums import ButtonStyle, TextStyle
from discord.ext import commands
import asyncio
import numpy as np
import time
import io

from belphegor.bot import Belphegor
from belphegor.ext_types import Interaction, TextInput
from belphegor.templates.buttons import InputButton
from belphegor.templates.views import StandardView, ContinuousInputView
from .misc_core import calculator

#=============================================================================================================================#

BOX_PATTERN = {
    (0, 0): " ",
    (0, 1): "\u2584",
    (1, 0): "\u2580",
    (1, 1): "\u2588"
}

#=============================================================================================================================#

class Misc(commands.Cog):
    def __init__(self, bot: Belphegor):
        self.bot = bot

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

    @ac.command(name = "calc")
    async def calc(
        self,
        interaction: Interaction
    ):
        m = calculator.MathParse()

        class MathView(ContinuousInputView):
            class InputButton(ContinuousInputView.InputButton):
                class InputModal(ContinuousInputView.InputButton.InputModal):
                    input = TextInput(
                        label = "Input formulas",
                        style = TextStyle.long,
                        min_length = 1,
                        max_length = 1000
                    )

        view = MathView(allowed_user = interaction.user)
        async for interaction, input in view.setup(interaction):
            inp = input.value
            try:
                start = time.perf_counter()
                r = await asyncio.get_running_loop().run_in_executor(None, m.result, inp)
                end = time.perf_counter()
                time_taken = end - start
            except calculator.ParseError as e:
                target = getattr(e, "target", m)
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
                target = getattr(e, "target", m)
                msg = f"Calculation error.\n```\n{target.show_parse_error()}\n```"
            except Exception as e:
                title = "Error"
                target = getattr(e, "target", m)
                msg = f"Parsing error.\n```\n{target.show_parse_error()}\n```"
            else:
                title = f"Result in {1000*(time_taken):.2f}ms"
                r = "\n".join(r)
                msg = f"```\n{r}\n```"

            e = discord.Embed(title = title)
            e.add_field(name = "Input", value = f"```\n{inp}\n```", inline = False)
            e.add_field(name = "Result", value = msg, inline = False)

            await view.response_to(interaction, embed = e)

#=============================================================================================================================#

async def setup(bot):
    await bot.add_cog(Misc(bot))
