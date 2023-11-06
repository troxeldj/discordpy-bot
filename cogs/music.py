import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
from yt_dlp import YoutubeDL


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the Music cog.

        Args:
            bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot

        # Holds Playing Status
        # Guild ID -> Bool
        self.is_playing = {}

        # Holds Paused Status
        # Guild ID -> Bool
        self.is_paused = {}

        # Holds Music Queue
        # Guild ID -> List of Music Objects
        self.musicQueue = {}

        # Holds queue Index
        # Guild ID -> Index (int)
        self.queueIndex = {}

        # Holds Connected VoiceChannel for a Guild
        # Guild ID -> VoiceClient Object
        self.vc = {}

        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {
            'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
            'options': '-vn'
        }

    def now_playing_embed(self, interaction: discord.Interaction, song: dict) -> discord.Embed:
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = interaction.user
        avatar = author.avatar

        embed = discord.Embed(
            title="Now Playing",
            description=f'[{title}]({link})',
            colour=self.embedBlue,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Called when the bot is ready.

        Initializes the music queue, queue index, and voice client for each guild that the bot is a member of.
        """
        print("Music cog is ready.")
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_playing[id] = self.is_paused[id] = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Called when a member's voice state changes.

        If the bot is the only member in a voice channel that a member leaves, the bot stops playing audio.

        Args:
            member (discord.Member): The member whose voice state changed.
            before (discord.VoiceState): The member's voice state before the change.
            after (discord.VoiceState): The member's voice state after the change.
        """
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()

    @discord.app_commands.command(name="join", description="Joins the current voice channel.")
    async def join(self, interaction: discord.Interaction) -> None:
        """
        Stops the current song.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        if interaction.user.voice:
            userChannel = interaction.user.voice.channel  # VoiceChannel Object
            # VoiceClient Object
            self.vc[guild_id] = await userChannel.connect()
            await interaction.response.send_message(f'Bot has joined {userChannel}')
        else:
            await interaction.response.send_message("You are not connected to a voice channel.")

    @discord.app_commands.command(name="leave", description="Disconnects from the current voice channel.")
    async def leave(self, interaction: discord.Interaction) -> None:
        """
        Disconnects from the current voice channel.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        if self.vc[guild_id] != None:
            await self.vc[guild_id].disconnect()
            await interaction.response.send_message("Bot has left the chat.")
            self.vc[guild_id] = None
        else:
            await interaction.response.send_message("Bot is not connected to a voice channel.")

    def search_YT(self, query: str) -> list:
        """
        Searches YouTube for videos matching a given query. Returns a list of up to 10 video URLs.

        Args:
            query (str): The search query.

        Returns:
            list: A list of up to 10 video URLs.
        """
        query = parse.quote(query)
        url = f"https://youtube.com/results?search_query={query}"
        response = request.urlopen(url)
        videos = re.findall(r"watch\?v=(\S{11})", response.read().decode())
        return [f"https://youtube.com/watch?v={video}" for video in videos][1:11]

    def isValidYTURL(self, url: str) -> bool:
        """
        Checks if a given URL is a valid YouTube URL.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is a valid YouTube URL, False otherwise.
        """
        return re.match(r"https://[www.]*youtube.com.*", url) != None

    def isYTVideoURL(self, url: str) -> bool:
        """
        Checks if a given URL is a YouTube video URL (youtube.com/watch).

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is a YouTube video URL, False otherwise.
        """
        return re.match(r"https:\/\/(www\.){0,1}youtube.com/watch.*", url) != None

    def isYTPlaylistURL(self, url: str) -> bool:
        """
        Checks if a given URL is a YouTube playlist URL (youtube.com/playlist).

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is a YouTube playlist URL, False otherwise.
        """
        return re.match(r"https:\/\/(www\.){0,1}youtube.com/playlist.*", url) != None

    async def getSongInfo(self, url: str, interaction: discord.Interaction):
        """
        Extracts information about a song from a given URL.

        Args:
            url (str): The URL of the song to extract information from.
            interaction (discord.Interaction): The interaction object.

        Returns:
            dict: A dictionary containing information about the song, including the stream URL, title, thumbnail URL, channel name, and link. Returns None if the song could not be downloaded.
        """
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                data = ydl.extract_info(url, download=False)
                song = {"stream_url": data['url'], "title": data['title'], "thumbnail_url": data['thumbnail'],
                        "channel_name": data['uploader'], "link": data['webpage_url']}
                song['stream_obj'] = discord.FFmpegPCMAudio(
                    song['stream_url'], **self.FFMPEG_OPTIONS)
                return song
            except:
                await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
                return

    # TODO: Fix up with above functions
    @discord.app_commands.command(name="play", description="Plays a song from a link.")
    async def play(self, interaction, query: str):
        """
        Plays a song from a given URL.

        Currently Supports:
        - Youtube Video URL
        - Youtube Playlist URL - Not yet implemented
        - Search Query - Not yet implemented

        Args:
            ctx (discord.ext.commands.Context): The context object.
            url (str): The URL of the song to play.
        """
        guild_id = int(interaction.guild.id)
        await interaction.response.defer()
        if interaction.user.voice == None:  # If user not in channel, send message and return
            await interaction.followup.send("You must be connected to a voice channel.")
            return

        if self.vc[guild_id] == None:  # If bot not in channel, join channel
            userChannel = interaction.user.voice.channel
            # VoiceClient Object
            self.vc[guild_id] = await userChannel.connect()
        else:  # If bot in diff channel, switch voice channel
            await self.vc[guild_id].move_to(userChannel)

        if self.isValidYTURL(query):  # Valid youtubeURL
            if self.isYTPlaylistURL(query):
                await interaction.followup.send("Playlist URL detected. This feature is not yet implemented.")
            elif self.isYTVideoURL(query):
                songInfo = await self.getSongInfo(query, interaction)
                if songInfo['stream_url'] == None:
                    await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
                    return
                self.musicQueue[guild_id].append(songInfo)
                if self.is_playing[guild_id] == False:
                    self.vc[guild_id].play(songInfo['stream_obj'])
                    self.is_playing[guild_id] = True
                    self.is_paused[guild_id] = False
                    await interaction.followup.send("Now playing!")
            else:
                await interaction.followup.send("Invalid Youtube URL. Please check your input and try again.")
        else:  # Requires searching
            urls = self.search_YT(query)
            print(urls)
            if len(urls) == 0:
                await interaction.followup.send("No results found. Try Again.")
                return
            songInfo = await self.getSongInfo(urls[0], interaction)
            if songInfo['stream_url'] == None:
                await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
                return
            self.musicQueue[guild_id].append(songInfo)
            if self.is_playing[guild_id] == False:
                self.vc[guild_id].play(songInfo['stream_obj'])
                self.is_playing[guild_id] = True
                self.is_paused[guild_id] = False
                await interaction.followup.send("Now playing!")

    @discord.app_commands.command(name="pause", description="Pauses the current song.")
    async def pause(self, interaction: discord.Interaction) -> None:
        """
        Pauses the current song.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        if self.is_playing[guild_id] == False:
            await interaction.response.send_message("There is no audio to be paused at the moment.")
        else:
            try:
                self.vc[guild_id].pause()
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = True
                await interaction.response.send_message("Audio paused!")
            except Exception as e:
                print(e)
                await interaction.response.send_message("Could not pause the song.")
                return

    @discord.app_commands.command(name="resume", description="Resumes the current song.")
    async def resume(self, interaction: discord.Interaction) -> None:
        """
        Resumes the current song.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        if self.is_paused[guild_id] == False:
            await interaction.response.send_message("There is no audio to be resumed at the moment.")
        else:
            try:
                self.vc[guild_id].resume()
                self.is_playing[guild_id] = True
                self.is_paused[guild_id] = False
                await interaction.response.send_message("Audio resumed!")
            except Exception as e:
                print(e)
                await interaction.response.send_message("Could not resume the song.")
                return

    @discord.app_commands.command(name="stop", description="Stops the current song.")
    async def stop(self, interaction: discord.Interaction) -> None:
        """
        Stops the current song.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        if self.is_playing[guild_id] == False:
            await interaction.response.send_message("There is no audio to be stopped at the moment.")
        else:
            try:
                self.vc[guild_id].stop()
                self.is_playing[guild_id] = False
                self.is_paused[guild_id] = False
                await interaction.response.send_message("Audio stopped!")
            except Exception as e:
                print(e)
                await interaction.response.send_message("Could not stop the song.")
                return
