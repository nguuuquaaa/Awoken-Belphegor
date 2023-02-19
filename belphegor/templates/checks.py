import discord
import typing

from collections.abc import Callable
from .discord_types import Interaction

#=============================================================================================================================#

def all(*checks: Callable):
    async def predicate(interaction: Interaction):
        for check in checks:
            if not await check(interaction):
                return False
        return True
    return predicate

def any(*checks: Callable):
    async def predicate(interaction: Interaction):
        for check in checks:
            if await check(interaction):
                return True
        return False
    return predicate

def user_only(user: discord.User) -> Callable:
    async def predicate(interaction: Interaction):
        return interaction.user == user
    return predicate

def owner_only():
    async def predicate(interaction: Interaction):
        return interaction.user.id == interaction.client.owner_id
    return predicate

def guild_manager_only():
    async def predicate(interaction: Interaction):
        return interaction.user.guild_permissions.manage_guild
    return predicate