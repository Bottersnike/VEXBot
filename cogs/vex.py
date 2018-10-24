import subprocess
import asyncio
import inspect
import time
import sys
import os

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


TRACK_GUILD = 498229213866754058


class VEX:
    VOICE_F = 'state/voice.txt'
    MSG_F = 'state/msg.txt'
    CHAR_F = 'state/char.txt'
    WORD_F = 'state/word.txt'

    def __init__(self, bot):
        self.bot = bot
        
        self.tracking = self.load_tracking()
        
        self.join_times = {}

    async def __local_check(self, ctx):
        return right_channel(ctx)

    def save_tracking(self):
        with open(self.VOICE_F, 'w') as voice:
            voice.write('\n'.join(f'{k}:{self.tracking["voice"][k]}' for k in self.tracking['voice']))
        with open(self.MSG_F, 'w') as msg:
            msg.write('\n'.join(f'{k}:{self.tracking["messages"][k]}' for k in self.tracking['messages']))
        with open(self.CHAR_F, 'w') as msg:
            msg.write('\n'.join(f'{k}:{self.tracking["chars"][k]}' for k in self.tracking['chars']))
        with open(self.WORD_F, 'w') as msg:
            msg.write('\n'.join(f'{k}:{self.tracking["words"][k]}' for k in self.tracking['words']))
    
    def load_tracking(self):
        tracking = {'voice': {}, 'messages': {}, 'words': {}, 'chars': {}}
        
        if os.path.exists(self.VOICE_F):
            with open(self.VOICE_F) as voice:
                for line in voice:
                    if not line.strip():
                        continue
                    tracking['voice'][int(line.split(':', 1)[0])] = int(line.split(':', 1)[1])

        if os.path.exists(self.MSG_F):
            with open(self.MSG_F) as msg:
                for line in msg:
                    if not line.strip():
                        continue
                    tracking['messages'][int(line.split(':', 1)[0])] = int(line.split(':', 1)[1])

        if os.path.exists(self.CHAR_F):
            with open(self.CHAR_F) as char:
                for line in char:
                    if not line.strip():
                        continue
                    tracking['chars'][int(line.split(':', 1)[0])] = int(line.split(':', 1)[1])

        if os.path.exists(self.WORD_F):
            with open(self.WORD_F) as word:
                for line in word:
                    if not line.strip():
                        continue
                    tracking['words'][int(line.split(':', 1)[0])] = int(line.split(':', 1)[1])
        
        return tracking
        
    async def on_message(self, message):
        if message.guild is not None and message.guild.id == TRACK_GUILD:
            if message.author.id not in self.tracking['messages']:
                self.tracking['messages'][message.author.id] = 0
            if message.author.id not in self.tracking['words']:
                self.tracking['words'][message.author.id] = 0
            if message.author.id not in self.tracking['chars']:
                self.tracking['chars'][message.author.id] = 0

            self.tracking['messages'][message.author.id] += 1
            self.tracking['chars'][message.author.id] += len(message.content)
            self.tracking['words'][message.author.id] += message.content.count(' ') + 1
            self.save_tracking()
    
    async def on_voice_state_update(self, member, before, after):
        if member.guild is not None and member.guild.id == TRACK_GUILD:
            if before.channel is None and after.channel is not None:
                self.join_times[member.id] = time.time()
            elif before.channel is not None and after.channel is None:
                if member.id in self.join_times:
                    time_spent = time.time() - self.join_times[member.id]
                    self.bot.logger.info(f'{member} just left {before.channel} after {time_spent} seconds')

                    if member.id not in self.tracking['voice']:
                        self.tracking['voice'][member.id] = 0
                    self.tracking['voice'][member.id] += round(time_spent)
                    self.save_tracking()
        
    @commands.command()
    async def top(self, ctx):
        if ctx.guild is None or ctx.guild.id != TRACK_GUILD:
            return

        msg = '**Tᴏᴘ Mᴇssᴀɢᴇ Cᴏᴜɴᴛs:**\n'
        counts = sorted(self.tracking['messages'].items(), key=lambda x: x[1], reverse=True)
        counts = counts[:10]
        
        for n, i in enumerate(counts):
            member = ctx.guild.get_member(i[0]) or i[0]
            member = str(member).replace('`', '')
            msg += f'#{n + 1}: `{member}` _({i[1]})_\n'
        
        await ctx.send(msg)
        
    @commands.command()
    async def vtop(self, ctx):
        if ctx.guild is None or ctx.guild.id != TRACK_GUILD:
            return

        msg = '**Tᴏᴘ Tɪᴍᴇ ɪɴ VC:**\n'
        counts = sorted(self.tracking['voice'].items(), key=lambda x: x[1], reverse=True)
        counts = counts[:10]
        
        for n, i in enumerate(counts):
            member = ctx.guild.get_member(i[0]) or i[0]
            member = str(member).replace('`', '')
            msg += f'#{n + 1}: `{member}` _({i[1]} seconds)_\n'
        
        await ctx.send(msg)
        
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
    bot.add_cog(VEX(bot))
