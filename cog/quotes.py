import discord
import sqlite3
import random, re
from discord.ext import commands

class Quotes():
    def __init__(self, tzuyu):
        """Quote your best lines!"""
        self.tzuyu = tzuyu

    @commands.group(brief="Used to access quotes.")
    @commands.guild_only()
    async def quote(self, ctx):
        """Command group to access quote-related commands. If no subcommand is provided, Tzuyu Bot will provide a random quote from this guild.

        For guild use only."""
        if ctx.invoked_subcommand is None:
            access = sqlite3.connect('quotes.db')
            desc = access.cursor().execute('SELECT rowid, quote, author FROM quotes WHERE guild=? ORDER BY RANDOM() LIMIT 1', (ctx.guild.id,)).fetchone()
            access.close()  
            if desc != None:
                embed = discord.Embed(description=desc[1], colour=0x28BAE3)
                embed.set_footer(text='{0[2]} [ID: {0[0]}]'.format(desc))
            else:
                embed = discord.Embed(description="No quotes found on this guild.", colour=0x28BAE3)
                embed.set_footer(text='Guild: {0.name} [{0.id}]'.format(ctx.guild))
            await ctx.send(embed=embed)
    
    @quote.command(brief="Adds quotes.")
    async def add(self, ctx, *, string):
        """Adds quotes to a guild-specific list. Ideal formatting: "quote" - author <year>. For guild use only."""
        seperator = string.rfind('-')
        substring = string[:seperator-1]
        startIndex = substring.find('\"')
        if startIndex != -1:
            endIndex = substring.find('\"', startIndex + 1)
            if endIndex != -1 and len(string[seperator:].rstrip().lstrip()) > 0:
                quote = substring[startIndex:endIndex + 1]
                author = string[seperator:]

                access = sqlite3.connect('quotes.db')
                access.cursor().execute('INSERT INTO quotes (guild, quote, author) VALUES (?, ?, ?)', (ctx.guild.id, quote, author))
                rowid = access.cursor().execute('SELECT rowid FROM quotes ORDER BY rowid DESC LIMIT 1').fetchone()[0]
                access.commit()
                access.close()

                embed = discord.Embed(title='Quote successfully added.', description=quote, colour=0x00FF00)
                embed.set_footer(text='{0} [ID: {1}]'.format(author, rowid))
                await ctx.send(embed=embed)
            else:
                raise discord.InvalidArgument("Quote not properly formatted")
        else:
            raise discord.InvalidArgument("Quote not properly formatted")

    @quote.command(brief="Removes quotes based on their ID.")
    async def remove(self, ctx, index : int):
        """Removes quotes based on their ID. You cannot remove quotes that are not associated with this guild. Guild use only."""
        access = sqlite3.connect('quotes.db')
        row = access.cursor().execute('SELECT rowid, * FROM quotes WHERE rowid=?', (index,)).fetchone()
        if row[1] == ctx.guild.id:
            access.cursor().execute('DELETE FROM quotes WHERE rowid=?', (index,))
            access.commit().close()
            embed = discord.Embed(title="Quote removed.", description='{0[2]} {0[3]}'.format(row), colour=0x00FF00)
            embed.set_footer(text=row[3])
        else:
            embed = discord.Embed(title="That quote isn't from this guild.", colour=0xFF0000)
        await ctx.send(embed=embed)

    @quote.command(brief="Used to search for quotes.")
    async def search(self, ctx, *, query):
        """Used to search for quotes. THe query can be anything, although only searches from this guild will be shown. For guild use only."""
        access = sqlite3.connect('quotes.db')
        output = ['`{0}`: {1} {2}'.format(*row) for row in access.cursor().execute('SELECT rowid, quote, author FROM quotes WHERE guild=?', (ctx.guild.id,)) if query in '{0[1]} {0[2]}'.format(row).lower()]
        access.close()

        desc = "\n".join(output) if len(output) > 0 else "No quotes found."
        embed = discord.Embed(title='Quotes (query="{0}")'.format(query), description=desc, colour=0x28BAE3)
        embed.set_footer(text="Guild: {0.name} [{0.id}]".format(ctx.guild), icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @quote.command(brief="View the quotes for a server.")
    async def view(self, ctx, page : int=1):
        """View the quotes for a server. Only quotes from this guild will be shown. For guild use only."""
        access = sqlite3.connect('quotes.db')
        quote_list = ['`{0}`: {1} {2}'.format(*row) for row in access.cursor().execute('SELECT rowid, quote, author FROM quotes WHERE guild=?', (ctx.guild.id,))]
        access.close()

        final = [quote_list[i:i + 10] for i in range(0, len(quote_list), 10)]
        correct_page = page if page <= len(final) else len(final)
        output = final[correct_page - 1]
        desc = "\n".join(output) if len(output) > 0 else "No quotes found."

        embed = discord.Embed(title="Quotes [Page {}/{}]".format(correct_page, len(final)), description=desc, colour=0x28BAE3)
        embed.set_footer(text="Guild: {0.name} [{0.id}]".format(ctx.guild), icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @quote.command(brief="View a specific quote.")
    async def get(self, ctx, index : int=-1):
        """View a specific quote. If no index is provided, I'll provide a random quote instead. Guild use only."""
        access = sqlite3.connect('quotes.db')
        if index == -1:
            desc = access.cursor().execute('SELECT rowid, quote, author FROM quotes WHERE guild=? ORDER BY RANDOM() LIMIT 1', (ctx.guild.id,)).fetchone()
            if desc != None:
                embed = discord.Embed(description=desc[1], colour=0x28BAE3)
                embed.set_footer(text='{0[2]} [ID: {0[0]}]'.format(desc))
            else:
                embed = discord.Embed(
                    description="No quote found.", colour=0x28BAE3)
                embed.set_footer(text='Guild: {0.name} [{0.id}]'.format(
                    ctx.guild))
        else:
            desc = access.cursor().execute('SELECT rowid, * FROM quotes WHERE rowid=?', (index,)).fetchone()
            if desc[1] != ctx.guild.id:
                embed = discord.Embed(title="This quote cannot be accessed in this guild.", colour=0xFF0000)
            else:
                embed = discord.Embed(description=desc[2], colour=0x28BAE3)
                embed.set_footer(text='{0[3]} [ID: {0[0]}]'.format(desc))
        access.close()
        await ctx.send(embed=embed)

def setup(tzuyu):
    tzuyu.add_cog(Quotes(tzuyu))
