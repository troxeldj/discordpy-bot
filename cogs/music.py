import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
from os import getenv
import googleapiclient.discovery

load_dotenv()
YOUTUBE_API_KEY = getenv('YOUTUBE_API_KEY')


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
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY)
        try:
            request = youtube.search().list(
                part="snippet",
                q=query
            )
            response = request.execute()
        except:
            return []
        return [f"https://www.youtube.com/watch?v={item['id']['videoId']}" for item in response['items']]

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

    async def getStreamURL(self, url: str, interaction: discord.Interaction) -> str:
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                stream_url = None
                data = ydl.extract_info(url, download=False)
                if data:
                    stream_url = data['url']
                return stream_url
            except:
                await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
                return

    def getSongInfo(self, url: str, interaction: discord.Interaction) -> dict:
        video_id = url.split("=")[1]
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()
        if response:
            return {"video_id": response['items'][0]['id'], "url": url, "title": response['items'][0]['snippet']['title'], "artist": response['items'][0]['snippet']['channelTitle'], "thumbnail": response['items'][0]['snippet']['thumbnails']['default']['url']}

    async def getPlaylistInfo(self, url: str, interaction: discord.Interaction) -> list:
        playlist_id = url.split("=")[1]
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.playlistItems().list(
            part="snippet",
            maxResults="50",
            playlistId=playlist_id
        )
        response = request.execute()
        nextPageToken = response.get('nextPageToken')
        while 'nextPageToken' in response:
            nextPage = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults="50",
                pageToken=nextPageToken
            ).execute()
            response['items'] = response['items'] + nextPage['items']
            if 'nextPageToken' not in nextPage:
                response.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']
        return response

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
        userChannel = interaction.user.voice.channel
        guild_id = int(interaction.guild.id)
        await interaction.response.defer()
        if interaction.user.voice == None:  # If user not in channel, send message and return
            await interaction.followup.send("You must be connected to a voice channel.")
            return

        if self.vc[guild_id] == None:  # If bot not in channel, join channel
            # VoiceClient Object
            self.vc[guild_id] = await userChannel.connect()
        else:  # If bot in diff channel, switch voice channel
            await self.vc[guild_id].move_to(userChannel)

        if self.isValidYTURL(query):  # Valid youtubeURL
            if self.isYTPlaylistURL(query):  # Playlist URL
                playListInfo = await self.getPlaylistInfo(query, interaction)
                if playListInfo == None:
                    await interaction.followup.send("Could not get playlist information. Please try again.")
                    return
                # Get URL for each song in playlist
                for item in playListInfo['items']:
                    url = f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}"
                    # Get Song Information -> {}
                    songInfo = {"title": item['snippet']['title'], "artist": item['snippet']
                                ['channelTitle'], "thumbnail": item['snippet']['thumbnails']['default']['url'], "url": url}
                    self.musicQueue[guild_id].append(songInfo)

                if self.is_playing[guild_id] == False:
                    songInfo = self.musicQueue[guild_id][self.queueIndex[guild_id]]
                    songInfo['stream_url'] = await self.getStreamURL(songInfo['url'], interaction)
                    self.vc[guild_id].play(discord.FFmpegPCMAudio(
                        songInfo['stream_url'], **self.FFMPEG_OPTIONS))
                    self.is_playing[guild_id] = True
                    self.is_paused[guild_id] = False
                    await interaction.followup.send("Now playing!")
                else:
                    await interaction.followup.send("Playlist added to queue.")
            elif self.isYTVideoURL(query):  # Video URL
                # Get Song Information -> {}
                try:
                    songInfo = self.getSongInfo(query, interaction)
                except Exception as e:
                    print(e)
                    await interaction.followup.send("Could not get song information. Please try again.")
                    return
                if songInfo['stream_url'] == None:
                    await interaction.followup.send("Could not find stream URL. Please try again.")
                    return

                # Add to Queue / Play
                self.musicQueue[guild_id].append(songInfo)
                if self.is_playing[guild_id] == False:
                    songInfo['stream_url'] = await self.getStreamURL(songInfo['url'], interaction)
                    if songInfo['stream_url'] == None:
                        await interaction.followup.send("Could not find stream URL. Please try again.")
                        return
                    self.vc[guild_id].play(discord.FFmpegPCMAudio(
                        songInfo['stream_url'], **self.FFMPEG_OPTIONS))
                    self.is_playing[guild_id] = True
                    self.is_paused[guild_id] = False
                    await interaction.followup.send("Now playing!")
            else:
                await interaction.followup.send("Song added to queue.")
        else:  # Requires searching
            # Search YT -> [urls]
            try:
                urls = self.search_YT(query)
            except:
                await interaction.followup.send("Could not search YouTube. Please try again.")
                return

            if len(urls) == 0:
                await interaction.followup.send("No Youtube Search results found. Try Again.")
                return

            # Get Song Information -> {}
            try:
                songInfo = self.getSongInfo(urls[0], interaction)
            except Exception as e:
                print(e)
                await interaction.followup.send("Could not get song information. Please try again.")
                return

            # Add to Queue / Play
            self.musicQueue[guild_id].append(songInfo)
            if self.is_playing[guild_id] == False:
                songInfo['stream_url'] = await self.getStreamURL(urls[0], interaction)
                if songInfo['stream_url'] == None:
                    await interaction.followup.send("Could not find stream URL. Please try again.")
                    return
                self.vc[guild_id].play(discord.FFmpegPCMAudio(
                    songInfo['stream_url'], **self.FFMPEG_OPTIONS))
                self.is_playing[guild_id] = True
                self.is_paused[guild_id] = False
                await interaction.followup.send("Now playing!")
            else:
                await interaction.followup.send("Song added to queue.")

            # songInfo = await self.getSongInfo(urls[0], interaction)
            # if songInfo['stream_url'] == None:
            #     await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
            #     return
            # self.musicQueue[guild_id].append(songInfo)
            # if self.is_playing[guild_id] == False:
            #     self.vc[guild_id].play(songInfo['stream_obj'])
            #     self.is_playing[guild_id] = True
            #     self.is_paused[guild_id] = False
            #     await interaction.followup.send("Now playing!")

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

    @discord.app_commands.command(name="queue", description="Displays the current music queue.")
    async def queue(self, interaction: discord.Interaction, num: str = "10") -> None:
        """
        Displays the current music queue.

        Args:
            interaction (discord.Interaction): The interaction object.
            num (str, optional): The number of songs to display. Defaults to 10.
        """
        guild_id = int(interaction.guild.id)
        if not num.isnumeric():
            await interaction.response.send_message("Invalid argument. Please enter a number.")
            return
        num = int(num)
        embed = discord.Embed(
            title="Music Queue",
            colour=discord.Colour.blue())
        if len(self.musicQueue[guild_id]) == 0:
            embed.add_field(name="No songs in queue.",
                            value="Add some songs with /play or /add.")
            await interaction.response.send_message(embed=embed)
            return
        # embed.thumbnail = self.musicQueue[guild_id][0]['thumbnail']
        for i in range(num):
            if i >= len(self.musicQueue[guild_id]):
                break
            embed.add_field(
                name=f"Song #{i+1}", value=f"{self.musicQueue[guild_id][i]['title']} - {self.musicQueue[guild_id][i]['artist']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="clear", description="Clears the current music queue.")
    async def clear(self, interaction: discord.Interaction) -> None:
        """
        Clears the current music queue.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        guild_id = int(interaction.guild.id)
        self.musicQueue[guild_id] = []
        self.queueIndex[guild_id] = 0
        await interaction.response.send_message("Music queue cleared!")
