import subprocess
import asyncio
import inspect
import sys

from discord.ext import commands
import ruamel.yaml as yaml
import discord

from .util.checks import right_channel, is_developer, is_owner


SELF_SETTING = {
    'y10': 494761507004088320,
    'y12': 494761657734791189,
    'builder': 494525550178729995,
    'coder': 494525300500201482,
    'mechanic': 494525175337844736,
    'driver': 494524660763852803,
}

KIERAN_ROLE_ID = 500000697522192405


class VEX:
    """Core commands"""
    async def __local_check(self, ctx):
        return right_channel(ctx)

    @commands.command()
    @is_developer()
    async def list_roles(self, ctx):
        if ctx.guild is None:
            return await ctx.send('Must be used in a guild')
        roles = '```'
        for role in ctx.guild.roles:
            roles += f'{role.name}: {role.id}\n'
        roles += '```'
        await ctx.send(roles)

    @commands.command()
    async def iam(self, ctx, *, role):
        if role not in SELF_SETTING:
            e = discord.Embed(title='No role found under that name', color=0xbb5555)
            await ctx.send(embed=e, delete_after=5)
            return await ctx.message.delete()
        
        role_id = SELF_SETTING[role]
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        
        await ctx.author.add_roles(role)
        e = discord.Embed(title='Added role succesfully!', color=0x55bbbb)
        await ctx.send(embed=e, delete_after=5)
        await ctx.message.delete()
    
    @commands.command()
    async def iamnot(self, ctx, *, role):
        if role not in SELF_SETTING:
            e = discord.Embed(title='No role found undr that name', color=0xbb5555)
            await ctx.send(embed=e, delete_after=5)
            return await ctx.message.delete()
            
        role_id = SELF_SETTING[role]
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        
        await ctx.author.remove_roles(role)
        e = discord.Embed(title='Removed role succesfully!', color=0x55bbbb)
        await ctx.send(embed=e, delete_after=5)
        await ctx.message.delete()
    
    @commands.command()
    async def roles(self, ctx):
        if ctx.guild is None:
            return

        e = discord.Embed(title='Roles setup for self-service:', color=0xffff00)
        for i in SELF_SETTING:
            role = discord.utils.get(ctx.guild.roles, id=SELF_SETTING[i])
            if role is not None:
                e.add_field(name=role.name, value=f'`{ctx.prefix}iam {i}`')
        
        await ctx.send(embed=e)
    
    async def on_member_join(self, member):
        if member.guild.id == 498229213866754058:
            await member.add_roles(discord.Object(KIERAN_ROLE_ID))

        
def setup(bot):
    bot.add_cog(VEX())