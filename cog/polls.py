import discord, asyncio
import sqlite3
import arrow
import unicodedata
from discord.ext import commands

class Polls():
    def __init__(self, tzuyu):
        """Create and manage polls."""
        self.tzuyu = tzuyu
        self.polls_task = tzuyu.loop.create_task(self.check_polls())

    @commands.group(brief="Used to manage polls.")
    @commands.guild_only()
    async def poll(self, ctx):
        """Command group to manage polls. If no subcommand is provided, Tzuyu Bot will list active polls on this guild."""
        if ctx.invoked_subcommand is None:
            parent = self.tzuyu.get_command('poll')
            embed = discord.Embed(colour=0x28BAE3)
            embed.set_author(name='Help', icon_url=self.tzuyu.user.avatar_url)
            embed.add_field(name='@{} {}'.format(self.tzuyu.user.name, parent.signature), value=parent.help, inline=False)
            output = ['`{}` - {}'.format(c.name, c.brief) for c in parent.walk_commands()]
            embed.add_field(name='Subcommands:', value='\n'.join(output), inline=False)
            await ctx.send(embed=embed)

    @poll.command(brief="Create a poll.")
    async def create(self, ctx, time : int, *, information):
        """Allows users to create polls. Time is the amount of time allocated for the poll to run in minutes. Values less than one result in an untimed poll.

        An example of how information should be formatted: `name="Poll Name" choices="Option 1", "Option 2", ..., "Option n"`. You can also add descriptions using `desc="...poll description..."` or specify a channel `channel="...channelid..."`."""
        poll_end = arrow.utcnow().shift(minutes=time).timestamp if time > 1 else 6665846396 # timestamp

        name_start = information.find('name="') + 6 # poll name
        name_end = information.find('"', name_start)
        name = information[name_start:name_end]

        opt_start = information[name_end:].find('choices="') + 9 # poll options
        opt = information[name_end:][opt_start:]
        option_list = []
        index = 0
        while True or len(option_list) < 26:
            next_index = opt.find('"', index)
            emoji = ':regional_indicator_{0}:'.format(chr(len(option_list) + 97))
            option_list.append('{0}: {1}'.format(emoji, opt[index:next_index]))
            index = next_index + 1
            if opt[index:].find(', "') > -1:
                n = opt[index:].find('"') + 1
                index = index + n
            else:
                break
        if len(option_list) > 26:
            raise discord.InvalidArgument('Maximum of 26 choices')

        desc_end = 0 # description
        description = ''
        if opt[index + 1:].startswith('desc="'):
            d = opt[index + 1:]
            desc_start = d.find('desc="') + 6
            desc_end = d.find('"', desc_start)
            description = d[desc_start:desc_end]
            desc_end = desc_end + 1
        else:
            description = None

        channel = '' # channel
        if opt[index + desc_end + 1:].lstrip().startswith('channel="'):
            c = opt[index + desc_end + 1:].lstrip()
            ch_start = c.find('channel="') + 9
            index = c.find('"', ch_start)
            channel = int(c[ch_start:index])
        else:
            channel = ctx.channel.id

        msg_channel = self.tzuyu.get_channel(channel)
        if msg_channel.guild != ctx.guild:
            raise discord.InvalidArgument('Specificed channel is not within this guild')

        em_desc = '\n'.join(option_list) if not description else '{0}\n{1}'.format(description, '\n'.join(option_list))
        embed = discord.Embed(title=name, description=em_desc, colour=0x28BAE3)

        conn = sqlite3.connect('polls.db')
        t = arrow.get(poll_end).format('YYYY-MM-DD HH:mm')
        rowid = conn.cursor().execute('SELECT rowid FROM polls ORDER BY rowid DESC LIMIT 1').fetchone()[0] + 1
        embed.set_footer(text='Expires on {0}. [ID: {1}]'.format(t, rowid))
        msg = await msg_channel.send(embed=embed)
        
        opt_string = '>|<'.join(option_list) # options will be a string joined by >|< for each choice
        conn.cursor().execute('INSERT INTO polls (timestamp, name, choices, description, creator, guild, channel, message) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                              (poll_end, name, opt_string, description, ctx.author.id, ctx.guild.id, msg_channel.id, msg.id))
        conn.commit()
        conn.close()

        if msg_channel != ctx.channel:
            embed2 = discord.Embed(title='Poll successfully created.', description='**{0}** was created in {1}.'.format(name, msg_channel.mention), colour=0x00FF00)
            embed2.set_footer(text='Expires on {0}. [ID: {1}]'.format(t, rowid))
            await ctx.send(embed=embed2)

    async def complete(self, row):
        original_channel = self.tzuyu.get_channel(row[7])
        original_message = await original_channel.get_message(row[8])
        choices = row[3].split('>|<')

        filtered_reactions = [x for x in original_message.reactions if unicodedata.name(x.emoji).lower().startswith('regional')]
        filtered_reactions.sort(key=lambda l: l.emoji, reverse=True) # sorts reations alphabetically

        # determines which choice is the winner
        highest = 0
        winner_id = 0
        for i in range(len(filtered_reactions)):
            answer = filtered_reactions[i]
            if answer.count > highest:
                highest = answer.count
                char = unicodedata.name(answer.emoji).lower()[-1:]
                winner_id = ord(char) - 97
        winner = choices[winner_id]

        # edit list of choices to reflect the winners and losers
        for i in range(len(choices)):
            if choices[i] == winner:
                choices[i] = '**{}**'.format(choices[i])
            else:
                choices[i] = '~~{}~~'.format(choices[i])
        
        # edit original poll method + create results
        if row[4] is None:
            completed = discord.Embed(title='[CLOSED] {}'.format(row[2]), description='\n'.join(choices), colour=0xFF0000)
            final = discord.Embed(title='[RESULTS] {}'.format(row[2]), description='\n'.join(choices), colour=0x28BAE3)
        else:
            completed = discord.Embed(title='[CLOSED] {}'.format(row[2]), description='{}\n{}'.format(row[4], '\n'.join(choices)), colour=0xFF0000)
            final = discord.Embed(title='[RESULTS] {}'.format(row[2]), description='{}\n{}'.format(row[4], '\n'.join(choices)), colour=0x28BAE3)
        completed.set_footer(text='Poll has expired.')

        await original_message.edit(embed=completed)
        await original_channel.send(embed=final)

        conn = sqlite3.connect('polls.db') # delete row
        conn.cursor().execute('DELETE FROM polls WHERE rowid=?', (row[0],))
        conn.commit()
        conn.close()

    @poll.command(brief="Ends a poll.")
    async def finish(self, ctx, index: int):
        """Ends a poll by specifiying its poll ID. This can be used to end untimed polls or prematurely end timed polls. You can only end polls that you have created."""
        conn = sqlite3.connect('polls.db')
        row = conn.cursor().execute('SELECT rowid, * FROM polls WHERE rowid=?', (index,)).fetchone()
        conn.close()

        if row[6] != ctx.guild.id:
            embed_err = discord.Embed(title="You can only finish polls in this guild.", colour=0xFF0000)
            return await ctx.send(embed=embed_err)
        elif row[5] != ctx.author.id:
            embed_err = discord.Embed(title="You can only remove your polls.", colour=0xFF0000)
            return await ctx.send(embed=embed_err)

        await self.complete(row)

    @poll.command(brief="View active polls.")
    async def view(self, ctx, index : int=-1):
        """View active polls on this guild. You can also view an individual poll by specifying its index."""
        conn = sqlite3.connect("polls.db")
        
        if index == -1:
            temp = []
            for row in conn.cursor().execute('SELECT rowid, name, guild, channel, message FROM polls WHERE guild=?', (ctx.guild.id,)):
                formatted = '{0} : {1} ([link](https://discordapp.com/channels/{2}/{3}?jump={4}))'.format(row[0], row[1], row[2], row[3], row[4])
                temp.append(formatted)
            desc = '\n'.join(temp) if len(temp) > 0 else "No polls found on this server."
            embed = discord.Embed(title="Polls", description=desc, colour=0x28BAE3)
            embed.set_footer(text='Guild: {0.name} [{0.id}]'.format(ctx.guild), icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            conn.close()
        else:
            row = conn.cursor().execute('SELECT timestamp, name, description, guild, channel, message FROM polls WHERE rowid=?', (index,)).fetchone()
            if row[3] == ctx.guild.id:
                if not row[2]:
                    embed = discord.Embed(title=row[1], description='[Click here to open the poll in your browser.](https://discordapp.com/channels/{}/{}?jump={})'.format(row[3], row[4], row[5]), colour=0x28BAE3)
                else:
                    embed = discord.Embed(title=row[1], description='{}\n[Click here to open the poll in your browser.](https://discordapp.com/channels/{}/{}?jump={})'.format(row[2], row[3], row[4], row[5]), colour=0x28BAE3)
                ts = arrow.get(row[0]).format('YYYY-MM-DD HH:mm')
                embed.set_footer(text='Expires on {}. [ID: {}]'.format(ts, index))
                await ctx.send(embed=embed)

    @poll.command(brief="Cancel a poll.")
    async def cancel(self, ctx, index: int=-1):
        """Cancels the poll with the provided poll ID. You can only cancel polls that you have created within the current guild."""
        conn = sqlite3.connect("polls.db")
        row = conn.cursor().execute("SELECT rowid, * FROM polls WHERE rowid=?", (index,)).fetchone()

        name = row[2]
        pollid = row[0]
        authorid = row[5]
        guildid = row[6]
        channelid = row[7]
        msgid = row[8]

        if ctx.author.id != authorid:
            embed = discord.Embed(title="You can only cancel polls that you create.", colour=0xFF0000)
            await ctx.send(embed=embed)
            conn.close()
            return
        if ctx.guild.id != guildid:
            embed = discord.Embed(title="You can only cancel polls in this guild.", colour=0xFF0000)
            await ctx.send(embed=embed)
            conn.close()
            return

        def check(message):
            return ctx.author.id == authorid

        embed = discord.Embed(title="Are you sure you would like to cancel this poll? (y/n)", description='{} : {}'.format(pollid, name), colour=0xFFFF00)
        await ctx.send(embed=embed)
        msg = await self.tzuyu.wait_for('message', check=check)

        if msg.content.rstrip().lstrip().lower()[0] != 'y':
            embed1 = discord.Embed(title='Poll was not cancelled.', colour=0xFF0000)
            await ctx.send(embed=embed1)
            conn.close()
        else:
            conn.cursor().execute('DELETE FROM polls WHERE rowid=?', (index,))
            conn.commit()
            conn.close()
            embed2 = discord.Embed(title="Poll successfully cancelled.", colour=0x00FF00)
            await ctx.send(embed=embed2)
            poll_channel = self.tzuyu.get_channel(channelid)
            to_edit = await poll_channel.get_message(msgid)
            embed0 = discord.Embed(title=name, description="Poll was cancelled.", colour=0xFF0000)
            await to_edit.edit(embed=embed0)

    async def check_polls(self):
        await self.tzuyu.wait_until_ready()
        while not self.tzuyu.is_closed():
            conn = sqlite3.connect('polls.db')
            for row in conn.cursor().execute('SELECT rowid, * FROM polls'):
                if row[1] <= arrow.utcnow().timestamp:
                    await self.complete(row)
            conn.close()
            await asyncio.sleep(30)

#https://discordapp.com/channels/208162050915041281/423123314030936064?jump=427654293315911691


def setup(tzuyu):
    tzuyu.add_cog(Polls(tzuyu))
