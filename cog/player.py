import discord, asyncio, itertools
from discord.ext import commands
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}
ytdl = YoutubeDL(ytdlopts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')
        self.duration = data.get('duration')
        self.skips = set()

    def __getitem__(self, item: str): # access attributes, only use when not downloading
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()
        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data: # first item in a playlist
            data = data['entries'][0]
        m, s = divmod(data['duration'], 60)
        time = '%02d:%02d' % (m, s)
        embed = discord.Embed(title='Added to Queue', description='**{}** [{}]'.format(data['title'], time), colour=0x28BAE3)
        embed.set_thumbnail(url=data['thumbnail'])
        embed.set_footer(text='Requested by {}.'.format(ctx.author))
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

    @classmethod
    async def regather_stream(cls, data, *, loop):
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']
        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)
        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)

class MusicPlayer:
    def __init__(self, ctx):
        self.neraina = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.np = None  # Now playing message
        self.volume = .1
        self.current = None

        self.neraina.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.neraina.wait_until_ready()

        while not self.neraina.is_closed():
            self.next.clear()
            try:
                async with timeout(300):
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.guild)

            if not isinstance(source, YTDLSource):
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.neraina
        .loop)
                except Exception:
                    raise discord.ext.commands.CommandError('Error processing song.')

            source.volume = self.volume
            self.current = source
            self.guild.voice_client.play(source, after=lambda _: self.neraina
.loop.call_soon_threadsafe(self.next.set))

            m, s = divmod(source.duration, 60)
            time = '%02d:%02d' % (m, s)
            embed = discord.Embed(title='Now Playing', description='**{}** [{}]'.format(source.title, time), colour=0x28BAE3)
            embed.set_thumbnail(url=source.thumbnail)
            embed.set_footer(text='Requested by {}.'.format(source.requester))
            self.np = await self.channel.send(embed=embed)
            await self.next.wait()

            source.cleanup()
            self.current = None

    def destroy(self, guild):
        return self.neraina.loop.create_task(self.cog.cleanup(guild))

class Player:
    def __init__(self, nerain):
        self.neraina = neraina
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
        return player
    
    def in_channel(self, voice):
        if not voice or not voice.is_connected():
            raise Exception('Not playing anything.')
        return True

    @commands.command(name='connect', aliases=['join', 'summon'], brief='Connects to a voice channel.')
    @commands.guild_only()
    async def voice_connect(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connects to a voice channel. If no channel is specified, this joins the user's current voice channel."""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise Exception('No channel to join.')

        vc = ctx.voice_client
        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise Exception('Timed out trying to join the channel')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise Exception('Timed out trying to join the channel')

    @commands.command(name='queue', aliases=['enqueue'], brief='Requests a song.')
    @commands.guild_only()
    async def voice_queue(self, ctx, *, search: str):
        """Request a song and add it to the queue. This command attempts to join a valid voice channel if the bot is not already in one. Uses YTDL to automatically search and retrieve a song."""
        await ctx.trigger_typing()
        vc = ctx.voice_client
        if not vc:
            await ctx.invoke(self.voice_connect)

        player = self.get_player(ctx)
        source = await YTDLSource.create_source(ctx, search, loop=self.neraina.loop, download=False)
        await player.queue.put(source)

    @commands.command(name='pause', brief='Pauses the audio player.')
    @commands.guild_only()
    async def voice_pause(self, ctx):
        """Pauses the audio player."""
        vc = ctx.voice_client
        if self.in_channel(vc) and not vc.is_paused():
            vc.pause()

    @commands.command(name='play', brief='Resumes playing music.')
    @commands.guild_only()
    async def voice_play(self, ctx):
        """Resumes playing music."""
        vc = ctx.voice_client
        if self.in_channel(vc) and vc.is_paused():
            vc.resume()

    @commands.command(name='skip', brief='Casts a skip vote.')
    async def voice_skip(self, ctx):
        """Casts a skip vote. After three votes, the song is skipped."""
        vc = ctx.voice_client
        self.in_channel(vc)

        if not vc.is_playing() and not vc.is_paused():
            raise Exception('Nothing to skip.')
        elif ctx.author == vc.source.requester:
            embed = discord.Embed(title='Skipping the current song.', description='Requester is skipping songs.', colour=0x28BAE3)
            await ctx.send(embed=embed)
            vc.stop()
        else:
            vc.source.skips.add(ctx.author.id)
            if len(vc.source.skips) >= 3:
                embed = discord.Embed(title='Skipping the current song.', description='3 skip votes reached.', colour=0x28BAE3)
                await ctx.send(embed=embed)
                vc.stop()
            else:
                embed = discord.Embed(title='Skip vote added.', description='{}/3 votes to skip **{}**.'.format(len(vc.source.skips), vc.source.title), colour=0x28BAE3)
                await ctx.send(embed=embed)

    @commands.command(name='songs', aliases=['playlist'], brief='Shows the upcoming songs.')
    @commands.guild_only()
    async def voice_songs(self, ctx):
        """Shows the upcoming songs."""
        vc = ctx.voice_client
        self.in_channel(vc)
        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title='There are no queued songs.', colour=0x28BAE3)
            return await ctx.send(embed=embed)

        upcoming = list(itertools.islice(player.queue._queue, 0, 10))
        fmt = '\n'.join('{}. **{}**'.format(i+1, upcoming[i]["title"]) for i in range(0, len(upcoming)))
        embed = discord.Embed(title='Upcoming Songs', description=fmt, colour=0x28BAE3)
        await ctx.send(embed=embed)

    @commands.command(name='playing', aliases=['current'], brief='Gets information about what is playing.')
    @commands.guild_only()
    async def voice_current(self, ctx):
        """Gets information about what is playing."""
        vc = ctx.voice_client
        self.in_channel(vc)

        player = self.get_player(ctx)
        if not player.current:
            raise Exception('Not playing anything.')
        try:
            await player.np.delete()
        except discord.HTTPException:
            pass
        m, s = divmod(vc.source.duration, 60)
        time = '%02d:%02d' % (m, s)
        embed = discord.Embed(title='Now Playing', description='**{}** [{}]'.format(vc.source.title, time), colour=0x28BAE3)
        embed.set_thumbnail(url=vc.source.thumbnail)
        embed.set_footer(text='Requested by {}. [{}/3 skips]'.format(vc.source.requester, len(vc.source.skips)))
        player.np = await ctx.send(embed=embed)

    @commands.command(name='volume', brief='Changes the player volume.')
    @commands.guild_only()
    async def change_volume(self, ctx, *, vol: float):
        """Change the player volume. This must be a value between 0 and 100."""
        vc = ctx.voice_client
        self.in_channel(vc)

        if not 0 <= vol < 101:
            raise discord.ext.commands.UserInputError('Volume must be a float between 0 and 100.')
        player = self.get_player(ctx)
        if vc.source:
            vc.source.volume = vol / 100
        player.volume = vol / 100
        embed = discord.Embed(title='Player volume set to {}%.'.format(vol), colour=0x28BAE3)
        await ctx.send(embed=embed)

    @commands.command(name='quit', aliases=['disconnect'], brief='Destroys the player.')
    @commands.guild_only()
    async def voice_quit(self, ctx):
        """Stop the currently playing song and destroy the player."""
        vc = ctx.voice_client
        self.in_channel(vc)
        await self.cleanup(ctx.guild)

def setup(nerai):
    neraina.add_cog(Player(neraina))
