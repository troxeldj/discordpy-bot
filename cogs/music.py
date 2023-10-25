import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.isPlaying = {}
        self.isPaused = {}
        
        self.musicQueue = {}
        self.queueIndex = {}

        self.vc = {}

        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Music cog is ready.")
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.isPlaying[id] = self.isPaused[id] = False
    
    async def join_vc(self, interaction, channel):
        id = int(interaction.guild.id)
        # If bot is not in voice channel join voice channel.
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            #Send message if unable to send voice channel.
            if self.vc[id] == None:
                await interaction.response.send_message("Could not join voice channel.")
                return
        # If bot is in voice channel move to new voice channel.
        else:
            await self.vc[id].move_to(channel)

    def get_YT_title(self, videoID):
        pass

    def search_YT(self, search):
        queryString = parse.urlencode({'search_query': search})
        htmlContent = request.urlopen('http://www.youtube.com/results?' + queryString)
        searchResults = re.findall(
            '/watch\?v=(.{11})', htmlContent.read().decode())
        return searchResults[0:10]
    
        
        
        
        
        