import discord
from discord import app_commands
import numpy as np

#=============================================================================================================================#

BOX_PATTERN = {
    (0, 0): " ",
    (0, 1): "\u2584",
    (1, 0): "\u2580",
    (1, 1): "\u2588"
}

#=============================================================================================================================#

class Misc(app_commands.Group):
    
    @app_commands.command(name="eca")
    @app_commands.describe(rule_number="Rule number")
    async def elementary_cellular_automaton(
        self,
        interaction: discord.Interaction,
        rule_number: app_commands.Range[int, 1, 255]
    ):
        width = 64
        height = 60

        rule = np.array([(rule_number>>i)&1 for i in range(8)], dtype=np.uint8).reshape((2, 2, 2))
        cells = np.random.randint(0, 2, size=(height, width), dtype=np.uint8)
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
        
        await interaction.response.send_message(out)

def setup(tree: app_commands.CommandTree):
    tree.add_command(Misc())
