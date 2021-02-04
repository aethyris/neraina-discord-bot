import discord
from discord.ext import commands
from pathlib import Path
import os, random

class Community():
    def __init__(self, neraina):
        """Commands for the community."""
        self.neraina = neraina
        self.neraina_list = os.listdir('images/neraina')

    @commands.command(brief="I did the math.")
    async def math(self, ctx):
        """I did the math."""
        await ctx.send(file=discord.File("images/math.png"))

    @commands.command(name="neraina", brief="Mianhae.")
    async def nerain_img(self, ctx):
        name = 'images/neraina/{}'.format(random.choice(self.neraina_list))
        await ctx.send(file=discord.File(name))

def setup(neraina):
    neraina.add_cog(Community(neraina))
