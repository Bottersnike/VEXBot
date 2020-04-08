import subprocess
import asyncio
import inspect
import sys

from discord.ext.commands import *
import ruamel.yaml as yaml
import discord

from .util.checks import is_developer, is_owner


class Misc(Cog):
    """mis commands"""
    @command(aliases=['info'])
    async def faq(self, ctx):
        '''Answers some FAQs'''

        e = discord.Embed(title='FAQ', colour=0xffeb3b)
        e.add_field(name="Is this always correct", value="""
No. These are just predictions based on a mathematical model.
The accuracy of the predictions is only as good as that model.
""".strip(), inline=False)
        e.add_field(name="So.. what model do you use?", value="""
Each team has two values associated with it. The first value is based on the average score that team achieves. The second value is based on the average proporition of points the opponoent team scores proporitional to the difference in scores and the average score for that whole competion.
Predicting the results for a match is a case of summing the first value, then subtracting a multiplier of the second, all weighted according to the number of teams in an alliance.
""".strip(), inline=False)
        e.add_field(name="Why does a team higher on the leaderboard score worse against one lower?", value="""
The leaderboard currently only takes into account the first of these two values, while score predictions take into account both. I'm working on fixing that at some point.
""".strip(), inline=False)

        await ctx.send(embed=e)

    @command()
    async def test_accuracy(self, ctx):
        return await ctx.send("todo: this")
        pred = ctx.bot.cogs["Predictions"].pred
        success = []

        for n, match in enumerate(pred.matches):
            red, blue = [] , []
            for i in pred.TEAMS:
                name = match[i]
                if name:
                    if i.startswith('red'):
                        red.append(pred.teams[name])
                    else:
                        blue.append(pred.teams[name])

            win_probability = pred.win_probability(red, blue)
            if win_probability > 50:
                success.append(match['redscore'] > match['bluescore'])
            elif win_probability == 50:
                success.append(match['redscore'] == match['bluescore'])
            else:
                success.append(match['redscore'] < match['bluescore'])

        await ctx.send(f'{round(sum(success) / len(success) * 100, 2)}%')


def setup(bot):
    bot.add_cog(Misc())
