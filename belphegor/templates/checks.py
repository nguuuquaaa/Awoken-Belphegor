import discord
from collections.abc import Callable
import functools

from belphegor.ext_types import Interaction

#=============================================================================================================================#

class Check:
    @staticmethod
    def all(*checks: Callable):
        async def predicate(interaction: Interaction):
            for check in checks:
                if not await check(interaction):
                    return False
            return True
        return predicate

    @staticmethod
    def user_only(user: discord.User) -> Callable:
        async def predicate(interaction: Interaction):
            return interaction.user == user
        return predicate

    @staticmethod
    def owner_only():
        async def predicate(interaction: Interaction):
            return interaction.user.id == interaction.client.owner_id
        return predicate
