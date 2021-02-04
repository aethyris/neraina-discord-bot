import discord, asyncio, arrow
from discord.ext import commands
import sqlite3

class Alarms():
    def __init__(self, neraina):
        """Set, view, and remove alarms."""
        self.neraina = neraina
        self.data = sqlite3.connect('alarms.db')
        self.alarm_task = neraina.loop.create_task(self.check_alarms())

    @commands.group(brief="Used to manage alarms.")
    async def alarm(self, ctx):
        """Used to manage alarms."""
        if ctx.invoked_subcommand is None:
            parent = self.neraina.get_command('alarm')
            embed = discord.Embed(colour=0x28BAE3)
            embed.set_author(name='Help', icon_url=self.neraina.user.avatar_url)
            embed.add_field(name='@{} {}'.format(self.neraina.user.name, parent.signature), value=parent.help, inline=False)
            output = ['`{}` - {}'.format(c.name, c.brief) for c in parent.walk_commands()]
            embed.add_field(name='Subcommands:', value='\n'.join(output), inline=False)
            await ctx.send(embed=embed)

    @alarm.command(name='add', brief="Adds alarms based on UTC-5.")  
    async def alarm_add(self, ctx, day, time, *, reason=None):
        """Adds alarms based on UTC-5. Time can be entered in this format: `YYYY-MM-DD HH:mm`."""
        full = day + " " + time
        t = arrow.get(full.rstrip(), 'YYYY-MM-DD HH:mm')
        if not reason:
            reason = 'Alarm!'
        self.data.cursor().execute('INSERT INTO alarms (userid, channelid, timestamp, reason) VALUES (?, ?, ?, ?)', (ctx.author.id, ctx.channel.id, t.timestamp, reason))
        self.data.commit()

        embed = discord.Embed(title='Alarm set.', description='{0} | {1} {2}'.format(t.format('YYYY-MM-DD HH:mm'), ctx.channel, reason), colour=0x00FF00)
        await ctx.send(embed=embed)

    @alarm.command(name='view', brief="Shows all alarms the user has set.")
    async def view(self, ctx):
        """Shows all the alarms that the user has set."""
        # alarms that the user owns
        alarm_list = list(self.data.cursor().execute('SELECT rowid, * FROM alarms WHERE userid=?', (ctx.author.id,)))

        # prints list
        formatted_list = []
        for each in alarm_list: # checks channel type
            channel = self.neraina.get_channel(each[2])
            ch_text = '{0.guild}[#{0.name}]'.format(channel) if isinstance(channel, discord.abc.GuildChannel) else 'DM'
            formatted_list.append('{0} : {1} | {2} - {3}'.format(
                each[0], arrow.get(each[3]).format('YYYY-MM-DD HH:mm'), ch_text, each[4]))

        desc = 'No alarms' if len(formatted_list) < 1 else '```{}```'.format('\n'.join(formatted_list))
        embed = discord.Embed(description=desc, colour=0x28BAE3)
        embed.set_author(name='{}\'s Alarms'.format(str(ctx.author)), icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @alarm.command(name='remove', brief="Removes the specified alarm.")
    async def alarm_remove(self, ctx, index : int):
        """Removes the specified alarm. You can only remove your alarms."""
        row = self.data.cursor().execute('SELECT rowid, * FROM alarms WHERE rowid=?', (index,)).fetchone()
        if row[0] != ctx.author.id:
            raise Exception('Don\'t try to get rid of things you don\'t own.')  
        self.data.cursor().execute('DELETE FROM alarms WHERE rowid=?', (index,))

        channel = self.neraina.get_channel(row[2])
        ch_text = '{0.guild}[#{0.name}]'.format(channel) if isinstance(channel, discord.abc.GuildChannel) else 'DM'
        val = '{0} : {1} | {2} - {3}'.format(row[0], arrow.get(row[3]).format('YYYY-MM-DD HH:mm'), ch_text, row[4])
        embed = discord.Embed(title='Alarm removed.', value=val, colour=0x00FF00)
        await ctx.send(embed=embed)

    async def check_alarms(self):
        await self.neraina.wait_until_ready()
        while not self.neraina.is_closed():
            for alarm in list(self.data.cursor().execute('SELECT rowid, * FROM alarms')):
                author = self.neraina.get_user(alarm[1])
                channel = self.neraina.get_channel(alarm[2])
                time = alarm[3]
                if time <= arrow.utcnow().timestamp:
                    await channel.send('{0}: {1}'.format(author.mention, alarm[4]))
                    self.data.cursor().execute('DELETE FROM alarms WHERE rowid=?', (alarm[0],))
                    self.data.commit()
            await asyncio.sleep(30)

def setup(neraina):
    neraina.add_cog(Alarms(neraina))
