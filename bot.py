import discord, asyncio, sqlite3, arrow
from discord.ext import commands
from rivescript import RiveScript
import ext.conversion, ext.search
import time

# load rivescript
rive = RiveScript(utf8=True)
rive.load_directory("./rive")
rive.sort_replies()

description = '''Neraina Bot is a command bot that can also be spoken to naturally.'''
neraina = commands.Bot(command_prefix=commands.when_mentioned, description=description)

startup_extensions = ["cog.admin", "cog.alarms", "cog.community", "cog.information", "cog.player", "cog.polls", "cog.quotes"]
interrupt_msg = ''
start_time = time.time()
version = '0.9.0'

def parse(text):
    """Parses the rivescript reply for any command trigger."""
    if text.startswith('[conv:'):
        text = ext.conversion.convertparse(text.rstrip())
    elif text.startswith('[srch:'):
        text = ext.search.searchparse(text.rstrip())
    return text

def interrupts(input):
    """Checks for keywords in text and updates interrupt_msg"""
    global interrupt_msg
    if 'list' in input and len(input) < 800 and 'make' not in input:
        interrupt_msg = 'I don\'t see a flamethrower on this list.'
        return True
    elif 'need a hug' in input:
        interrupt_msg = 'Someone doesn\'t need a hug.'
        return True
    elif 'kms' in input or 'kys' in input or 'kill me' in input:
        interrupt_msg = 'Do you prefer stabbing or shooting?'
        return True
    elif 'cancer' in input:
        interrupt_msg = 'You are the cancer.'
        return True
    elif 'no regret' in input:
        interrupt_msg = 'You should.'
        return True
    else:
        return False

@neraina.event
async def on_ready():
    print("Connected as {0} (ID: {1})\n----------".format(neraina.user.name, str(neraina.user.id)))

@neraina.event
async def on_message(message):
    if not (message.content.lower().startswith("<@" + str(neraina.user.id) + ">") \
        or message.content.lower().startswith("<@!" + str(neraina.user.id) + ">")):
        return
    if message.author == neraina.user:
        return

    msg_no_mention = message.content[22:].lstrip()
    msg_no_mention_first = msg_no_mention.split()[0] if len(msg_no_mention.rstrip()) > 1 else ''
    if not neraina.get_command(msg_no_mention_first):
        reply = rive.reply("Aethyris", msg_no_mention)
        if reply.startswith('['):
            reply = parse(reply)
        await message.channel.send(reply)
    elif interrupts(msg_no_mention):
        await message.channel.send(interrupt_msg)
    else:
        await neraina.process_commands(message)

@neraina.event
async def on_command_error(ctx, error):
    command = ctx.command
    embed = discord.Embed(title='{}'.format(error), description='Use `@{} help {}` for more assistance.'.format(neraina.user.name, command), colour=0xFF0000)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    neraina.remove_command('help')
    for extension in startup_extensions:
        try:
            neraina.load_extension(extension)
            print('Cog loaded: {0}.'.format(extension))
        except Exception as e:
            exc = '{0}: {1}'.format(type(e).__name__, e)
            print('Failed to load cog {0}\n{1}'.format(extension, exc))

    neraina.run('') #discord api key