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
    def any(*checks: Callable):
        async def predicate(interaction: Interaction):
            for check in checks:
                if await check(interaction):
                    return True
            return False
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

    @staticmethod
    def guild_manager_only():
        async def predicate(interaction: Interaction):
            return interaction.user.guild_permissions.manage_guild
        return predicate