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

        e = discord.Embed(title='Leaderboard', colour=0xffeb3b)
        e.add_field(name="Is this always correct", value="""
No. These are just predictions based on a mathematical model.
The accuracy of the predictions is only as good as that model.
""".strip(), inline=False)
        e.add_field(name="So.. what model do you use?", value="""
Every team has two values associated with them. There's the "goodness" score of a team, `mu`, and the "confidence in the goodness score", `sigma`.
These two values form a normal distribution for each team. The `sigma` value will typically depend both on how many matches the team has taken part in, and how reliably they can reproduce the same score.
An idea team would have a high `mu` value, and a low `sigma`. When the bot loads in new data, it takes 10 minutes or so to process every single match it's able to, and from that calculates these two values.
""".strip(), inline=False)
        e.add_field(name="What's the leaderboard then?", value="""
The leaderboard is roughly based off a team's `mu` value.
""".strip(), inline=False)
        e.add_field(name="Why does a team higher on the leaderboard score worse against one lower?", value="""
When predicting a match, the reliability of a team is taken into account. If one team scores highly, but unreliably, while another scores a little lower, but reliably, the highest scoring team may not always be predicted to win.
""".strip(), inline=False)
        e.add_field(name="Can I view the mu and sigma values for a team?", value="""
I'm working on adding a command for just that. For now, if you DM me I can manually export them for specific teams.
""".strip(), inline=False)

        await ctx.send(embed=e)


def setup(bot):
    bot.add_cog(Misc())
