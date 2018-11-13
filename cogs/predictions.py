import subprocess
import asyncio
import inspect
import time
import sys
import os

from discord.ext import commands
import ruamel.yaml as yaml
import discord

from .util.checks import right_channel
from .util.predict import Predictor


class Predictions:
    def __init__(self, bot):
        self.bot = bot

        self.pred = Predictor()

    async def __local_check(self, ctx):
        return right_channel(ctx)

    @commands.command()
    async def leaderboard(self, ctx, team=None):
        """Show the predicted international leaderboard."""
        leaderboard = self.pred.generate_leaderboard()

        if team is not None:
            team = team.upper()
            if team not in leaderboard:
                e = discord.Embed(colour=0xff7043)
                e.description = f'Unknown team {team}.'

                return await ctx.send(embed=e)

            e = discord.Embed(colour=0xffeb3b)
            e.description = f'I have {team} as being in place #{leaderboard.index(team) + 1}'

            return await ctx.send(embed=e)

        e = discord.Embed(title='Leaderboard', colour=0xffeb3b)
        desc = ''
        for i in range(10):
            desc += f'{i + 1}: {leaderboard[i]}\n'
        e.description = desc

        await ctx.send(embed=e)

    @commands.command()
    async def predict(self, ctx, red, blue):
        """Predict the results of a match between two alliances.
        Alliances should be comma seperated lists of teams with no spaces.

        e.g. `predict 6969A,6969B 420C,420D`"""

        red, blue = red.upper(), blue.upper()
        red, blue = red.split(','), blue.split(',')

        for i in red + blue:
            if i not in self.pred.teams:
                e = discord.Embed(colour=0xff7043)
                e.description = f'Unknown team {i}.'

                return await ctx.send(embed=e)

        red_ts, blue_ts = [self.pred.teams[i] for i in red], [self.pred.teams[i] for i in blue]

        win_probability = round(self.pred.win_probability(red_ts, blue_ts) * 100, 2)

        e = discord.Embed()
        if win_probability == 50:
            e.description = 'I reckon it\'d be a perfect **draw**!'
            e.colour = 0x4caf50
        elif win_probability > 50:
            e.description = f'I reckon red have a **{win_probability}%** chance of winning'
            e.colour = 0xe53935
        else:
            e.description = f'I reckon blue have a **{100 - win_probability}%** chance of winning'
            e.colour = 0x3f51b5

        e.set_footer(text='Red: ' + ', '.join(red) + ' - Blue: ' + ', '.join(blue))

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Predictions(bot))