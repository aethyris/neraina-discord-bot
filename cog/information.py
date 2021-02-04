import discord
from discord.ext import commands
from bot import startup_extensions, version, start_time
import time

class Information:
    def __init__(self, neraina):
        """These commands are used for information about users, channels, or guilds."""
        self.neraina = neraina

    @commands.command(brief="Gives information about the user.")
    async def me(self, ctx):
        """Gives information about the author of the message. Includes ID and account creation date.
        
        If this used within a guild, also includes guild join date and roles."""
        embed = discord.Embed(colour=0x28BAE3)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.add_field(name='User ID', value=ctx.author.id, inline=True)
        embed.add_field(name='Creation Date', value=ctx.author.created_at.strftime(
            '%m/%d/%Y'), inline=True)
        roles = []
        if ctx.guild != None:
            embed.add_field(name='Join Date', value=ctx.author.joined_at.strftime('%m/%d/%Y'), inline=True)
            for index in range(len(ctx.author.roles)):
                roles.append(ctx.author.roles[index].name)
            roles.remove('@everyone')
            embed.add_field(name='Roles', value=", ".join(roles), inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief="Gives information about a guild member.")
    @commands.guild_only()
    async def user(self, ctx, *, member : discord.Member=None):
        """Gives information about a user. Includes their ID, account creation date, guild join date, and guild roles.
        
        If no member is mentioned, this gives information about the user of the command. Guild use only."""
        if not member:
            member = ctx.author

        embed = discord.Embed(colour=0x28BAE3)
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name='User ID', value=member.id, inline=True)
        embed.add_field(name='Creation Date', value=member.created_at.strftime(
            '%m/%d/%Y'), inline=True)
        roles = []
        embed.add_field(name='Join Date', value=member.joined_at.strftime('%m/%d/%Y'), inline=True)
        for index in range(len(member.roles)):
            roles.append(member.roles[index].name)
        roles.remove('@everyone')
        embed.add_field(name='Roles', value=", ".join(roles), inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief="Gives information about a channel.")
    @commands.guild_only()
    async def channel(self, ctx, *, channel : discord.TextChannel=None):
        """Gives information about a channel's ID and creation date. This can only be used for text channels within the current guild.
        
        If no channel is mentioned, information is provided about the current channel. Guild use only."""
        if not channel:
            channel = ctx.channel
        
        embed = discord.Embed(dscription=channel.topic, colour=0x28BAE3)
        embed.set_author(name='#' + channel.name, icon_url=channel.guild.icon_url)
        embed.add_field(name='Channel ID', value=channel.id, inline=True)
        embed.add_field(name='Creation Date', value=channel.created_at.strftime(
            '%m/%d/%Y'), inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief="Gives information about the current guild.")
    @commands.guild_only()
    async def server(self, ctx):
        """Gives information about the current guild. Includes server ID, owner, and creation date. Also lists the amount of members, roles, and emojis.
        
        For guild use only."""
        embed = discord.Embed(colour=0x28BAE3)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.add_field(name='ID', value=ctx.guild.id, inline=False)
        embed.add_field(name='Channels', value=str(
                len(ctx.guild.text_channels) + len(ctx.guild.voice_channels)), inline=True)
        embed.add_field(name='Members', value=str(
                len(ctx.guild.members)), inline=True)
        embed.add_field(name='Roles', value=str(
                len(ctx.guild.roles)), inline=True)
        embed.add_field(name='Emojis', value=str(
                len(ctx.guild.emojis)), inline=True)
        embed.add_field(name='Owner', value=ctx.guild.owner.name, inline=True)
        embed.add_field(name='Creation Date', value=ctx.guild.created_at.strftime(
                '%m/%d/%Y'), inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief="Gives information about Neraina Bot.")
    async def bot(self, ctx):
        """Gives information about Neraina Bot."""
        total = time.time() - start_time
        days = total / 86400
        days_sec = total % 86400
        hours = days_sec / 3600
        hours_sec = days_sec % 3600
        minutes = hours_sec / 60
        minutes_sec = hours_sec % 60
        seconds = minutes_sec % 60
        runtime = '{:1.0f}d {:1.0f}h {:1.0f}m {:1.0f}s'.format(
            days, hours, minutes, seconds)

        embed = discord.Embed(
            description="Neraina Bot is a command bot that can also be spoken to naturally.", colour=0x28BAE3)
        embed.set_author(
            name='neraina Bot', icon_url='https://cdn.discordapp.com/avatars/423160005181833216/7df401f4ef89fdfb26c4c32fda0ab57f.webp?size=1024')
        embed.add_field(name='Cogs:', value=', '.join(startup_extensions), inline=True)
        embed.add_field(name='Version:', value=version, inline=True)
        embed.add_field(name='Library:', value='discord.py ' + str(discord.__version__), inline=True)
        embed.add_field(name='Uptime:', value=runtime, inline=True)
        embed.set_image(
            url='https://www.sbs.com.au/popasia/sites/sbs.com.au.popasia/files/styles/full/public/twice-neraina-7.jpg')
        await ctx.send(embed=embed)     

    @commands.command(brief="Gives a list of a user's permissions.")
    @commands.guild_only()
    async def permissions(self, ctx, member : discord.Member=None):
        """Gives a list of the user's permissions. If no member is mentioned, gives the author's permissions."""
        if not member:
            member = ctx.author

        perms = '\n'.join(perm for perm, value in member.permissions_in(ctx.channel) if value)
        embed = discord.Embed(description=perms, colour=0x28BAE3)
        embed.set_author(icon_url=member.avatar_url, name=str(member))
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(brief="Shows this message.")
    async def help(self, ctx, command=None):
        """Shows this command. You can also use this command for more information about a cog or command."""
        if command is None:
            embed = discord.Embed(description=self.neraina.description, colour=0x28BAE3)
            embed.set_author(name='Help', icon_url=self.neraina.user.avatar_url)
            for ext_name in startup_extensions:
                output = []
                for command in list(self.neraina.get_cog_commands(ext_name[4:].title())):
                    if not command.hidden:
                        output.append('`{}` - {}'.format(command.name, command.brief))
                        output.sort()
                if len(output) > 0:
                    embed.add_field(name=ext_name[4:].title(), value='\n'.join(output), inline=False)
            embed.set_footer(text='Use @{} help <command|cog> for more assistance.'.format(self.neraina.user.name))
            await ctx.send(embed=embed)

        elif self.neraina.get_cog(command) is not None:
            embed = discord.Embed(colour=0x28BAE3)
            embed.set_author(name='Help', icon_url=self.neraina.user.avatar_url)
            output = []
            for each in list(self.neraina.get_cog_commands(command)):
                if not each.hidden:
                    output.append('`{}` - {}'.format(each.name, each.brief))
                    output.sort()
            if len(output) > 0:
                embed.add_field(name=command, value='\n'.join(output))
            else:
                embed.add_field(name=command, value="This cog has no visible commands.")
            embed.set_footer(text='Use @{} help <command|cog> for more assistance.'.format(self.neraina.user.name))
            await ctx.send(embed=embed)

        elif self.neraina.get_command(command):
            embed = discord.Embed(colour=0x28BAE3)
            embed.set_author(name='Help', icon_url=self.neraina.user.avatar_url)
            parent = self.neraina.get_command(command)
            try: # if its a group
                children = [each for each in parent.walk_commands()]
                children_names = [each.name for each in children]
                cmd = ctx.message.content[ctx.message.content.find('help') + 5:].split()
                if len(cmd) > 1: # command with child
                    if cmd[1] in children_names: 
                        index = children_names.index(cmd[1])
                        final = children[index]
                        embed.add_field(name='@{} {}'.format(self.neraina.user.name, final.signature), value=final.help, inline=False)
                else: # parent group when no child command is found
                    embed.add_field(name='@{} {}'.format(self.neraina.user.name, parent.signature), value=parent.help, inline=False)
                    output = ['`{}` - {}'.format(c.name, c.brief) for c in children]
                    embed.add_field(name='Subcommands:', value='\n'.join(output), inline=False)
                await ctx.send(embed=embed)
            except: # group or command
                embed.add_field(name='@{} {}'.format(self.neraina.user.name, parent.signature), value=parent.help, inline=False)
                await ctx.send(embed=embed)

        else:
            embed = discord.Embed(description="I couldn't find that category or command.", colour=0xFF0000)
            embed.set_author(name='Help', icon_url=self.neraina.user.avatar_url)
            await ctx.send(embed=embed)

def setup(neraina):
    neraina.add_cog(Information(neraina))
