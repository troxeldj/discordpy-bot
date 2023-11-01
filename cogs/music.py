import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
from yt_dlp import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_paused = {}
        
        self.musicQueue = {}
        self.queueIndex = {}

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
        # Holds Connected VoiceChannel for a Guild
        # Guild ID -> VoiceClient Object
        self.vc = {}

    def now_playing_embed(self, interaction, song):
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
        print("Music cog is ready.")
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_playing[id] = self.is_paused[id] = False
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()
    
    @discord.app_commands.command(name="join", description="Joins the current voice channel.")
    async def join(self, interaction):
        guild_id = int(interaction.guild.id)
        if interaction.user.voice:
            userChannel = interaction.user.voice.channel # VoiceChannel Object
            self.vc[guild_id] = await userChannel.connect() #VoiceClient Object
            await interaction.response.send_message(f'Bot has joined {userChannel}')
        else:
            await interaction.response.send_message("You are not connected to a voice channel.")
    
    @discord.app_commands.command(name="leave", description="Disconnects from the current voice channel.")
    async def leave(self, interaction):
        guild_id = int(interaction.guild.id)
        if self.vc[guild_id] != None:
            await self.vc[guild_id].disconnect()
            await interaction.response.send_message("Bot has left the chat.")
            self.vc[guild_id] = None
        else:
            await interaction.response.send_message("Bot is not connected to a voice channel.")

    @discord.app_commands.command(name="play", description="Plays a song from a link.")
    async def play(self, interaction, url: str):
        guild_id = int(interaction.guild.id)
        await interaction.response.defer()
        if interaction.user.voice == None: # If user not in channel, return
            await interaction.followup.send("You must be connected to a voice channel.")
            return
        
        if self.vc[guild_id] == None: # If bot not in channel, join channel
            userChannel = interaction.user.voice.channel
            self.vc[guild_id] = await userChannel.connect()
        else: # If bot in diff channel, switch voice channel
            await self.vc[guild_id].move_to(interaction.user.voice.channel)

        # Get song information
        with YoutubeDL (self.YTDL_OPTIONS) as ydl:
            try:
                data = ydl.extract_info(url, download=False)
                filename = data['url']
            except:
                await interaction.followup.send("Could not download the song. Incorrect format, try some different keywords.")
                return
        
        # Play Song
        try:
            self.vc[guild_id].play(discord.FFmpegPCMAudio(filename, **self.FFMPEG_OPTIONS))
            await interaction.followup.send("Now playing!")
            self.is_playing[guild_id] = True
        except Exception as e:
            print(e)
            await interaction.followup.send("Could not play the song. Incorrect format, try some different keywords.")
            return
    
    @discord.app_commands.command(name="pause", description="Pauses the current song.")
    async def pause(self, interaction):
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
    async def resume(self, interaction):
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
    async def stop(self, interaction):
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