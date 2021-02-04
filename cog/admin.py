import discord
from discord.ext import commands
from bot import startup_extensions
import arrow, time

class Admin:
    def __init__(self, neraina):
        """Administrative commands. Usually for admin or mod use only."""
        self.neraina = neraina

    @commands.command(hidden=True, brief="Used to reload cogs.")
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, cog=None):
        """Used to reload cogs. If a cog filename is passed as an argument, only that cog is reloaded; otherwise, all cogs are reloaded."""
        print('{0}: [{1.guild} #{1.channel}] {1.author} used {1.command}.'.format(arrow.get(ctx.message.created_at).to('US/Eastern').format('YYYY-MM-DD hh:mm:ss A'), ctx))
        if cog is None:
            success = []
            failure = []
            for cog in startup_extensions:
                try:
                    self.neraina.unload_extension(cog)
                    self.neraina.load_extension(cog)
                    success.append(cog)
                except Exception as e:
                    failure.append(cog)
                    print('Failed to load cog {0}: {1}'.format(cog, e))
            if len(success) > 0:
                embed = discord.Embed(colour=0x00FF00)
                embed.add_field(name='Successfully reloaded:', value=", ".join(success), inline=False)
                print('Cogs reloaded: {}'.format(', '.join(success)))
                await ctx.send(embed=embed)
            if len(failure) > 0:
                embed = discord.Embed(colour=0xFF0000)
                embed.add_field(name='Failed to reload:', value=", ".join(failure), inline=False)
                await ctx.send(embed=embed)
            await ctx.send(embed=embed)
        else:
            try:
                self.neraina.unload_extension(cog)
                self.neraina.load_extension(cog)
                print('Cog reloaded: {}.'.format(cog))
                embed = discord.Embed(colour=0x00FF00)
                embed.add_field(name='Successfully reloaded: ', value=cog, inline=False)
                await ctx.send(embed=embed)
            except Exception as e:
                print('Failed to reload cog {0}: {1}'.format(cog, e))
                embed = discord.Embed(colour=0xFF0000)
                embed.add_field(name='Failed to reload: ', value=cog, inline=False)
                await ctx.send(embed=embed)
    
    @commands.command(hidden=True, brief="Unloads a single cog.")
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, cog):
        """Used to unload a single cog."""
        print('{0}: [{1.guild} #{1.channel}] {1.author} used {1.command}.'.format(arrow.get(
        ctx.message.created_at).to('US/Eastern').format('YYYY-MM-DD hh:mm:ss A'), ctx))
        try:
            self.neraina.unload_extension(cog)
            print('Cog unloaded: {}.'.format(cog))
            embed = discord.Embed(colour=0x00FF00)
            embed.add_field(name='Successfully unloaded: ', value=cog, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            print('Failed to unload cog {0}: {1}'.format(cog, e))
            embed = discord.Embed(colour=0xFF0000)
            embed.add_field(name='Failed to unload: ', value=cog, inline=False)
            await ctx.send(embed=embed)

    @commands.command(hidden=True, brief='Load a single cog.')
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, cog):
        """Used to load a single cog."""
        print('{0}: [{1.guild} #{1.channel}] {1.author} used {1.command}.'.format(arrow.get(
            ctx.message.created_at).to('US/Eastern').format('YYYY-MM-DD hh:mm:ss A'), ctx))
        try:
            self.neraina.load_extension(cog)
            print('Cog loaded: {}.'.format(cog))
            embed = discord.Embed(colour=0x00FF00)
            embed.add_field(name='Successfully loaded: ',
                            value=cog, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            print('Failed to load cog {0}: {1}'.format(cog, e))
            embed = discord.Embed(colour=0xFF0000)
            embed.add_field(name='Failed to load: ', value=cog, inline=False)
            await ctx.send(embed=embed)
   
    @commands.command(hidden=True, brief="Delete messages from the channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def clean(self, ctx, amount : int, member: discord.Member=None):
        """Deletes messages from the channel this command was used in. If a member is specified, only messages by that member are deleted."""
        def check(message):
            return message.author == ctx.author
        def is_member(message):
            return message.author == member

        embed0 = discord.Embed(title='Do you want to delete up to {} message(s)?'.format(amount), colour=0xFFFF00)        
        await ctx.send(embed=embed0)
        msg = await self.neraina.wait_for('message', check=check)

        if msg.content.rstrip().lstrip().lower()[0] != 'y':
            await ctx.channel.purge(limit=2)
            embed1 = discord.Embed(title='I was looking forward to that.', colour=0xFF0000)
            return await ctx.send(embed=embed1)

        deleted_list = []
        if not member:
            deleted_list = await ctx.channel.purge(limit=amount+3)
        else:
            deleted_list = await ctx.channel.purge(limit=amount+3, check=is_member)
        embed1 = discord.Embed(title='{0} deleted {1} message(s).'.format(str(ctx.author), len(deleted_list)), colour=0x00FF00)
        await ctx.send(embed=embed1)

def setup(neraina):
    neraina.add_cog(Admin(neraina))
