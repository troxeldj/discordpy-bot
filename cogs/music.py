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

      
        # def added_song_embed(self, interaction, song):
        #     title = song['title']
        #     link = song['link']
        #     thumbnail = song['thumbnail']
        #     author = interaction.user
        #     avatar = author.avatar

        #     embed = discord.Embed(
        #         title="Song Added To Queue!",
        #         description=f'[{title}]({link})',
        #         colour=self.embedRed,
        #     )
        #     embed.set_thumbnail(url=thumbnail)
        #     embed.set_footer(text=f'Song added by: {str(author)}', icon_url=avatar)
        #     return embed
    
    
    
    # def removed_song_embed(self, interaction, song):
    #     title = song['title']
    #     link = song['link']
    #     thumbnail = song['thumbnail']
    #     author = interaction.user
    #     avatar = author.avatar

    #     embed = discord.Embed(
    #         title="Song Removed From Queue!",
    #         description=f'[{title}]({link})',
    #         colour=self.embedRed,
    #     )
    #     embed.set_thumbnail(url=thumbnail)
    #     embed.set_footer(
    #         text=f'Song removed by: {str(author)}', icon_url=avatar)
    #     return embed


    # async def join_VC(self, interaction, channel):
    #     id = int(interaction.guild.id)
    #     # If bot is not in voice channel join voice channel.
    #     if self.vc[id] == None or not self.vc[id].is_connected():
    #         self.vc[id] = await channel.connect()

    #         #Send message if unable to send voice channel.
    #         if self.vc[id] == None:
    #             await interaction.response.send_message("Could not join voice channel.")
    #             return
    #     # If bot is in voice channel move to new voice channel.
    #     else:
    #         await self.vc[id].move_to(channel)

    # # Gets title from youtube video ID.
    # def get_YT_title(self, videoID):
    #     params = {"format": "json",
    #               "url": "https://www.youtube.com/watch?v=%s" % videoID}
    #     url = "https://www.youtube.com/oembed"
    #     queryString = parse.urlencode(params)
    #     url = url + "?" + queryString
    #     with request.urlopen(url) as response:
    #         responseText = response.read()
    #         data = json.loads(responseText.decode())
    #         return data['title']
    
    # def extract_YT(self, url):
    #     with YoutubeDL(self.YTDL_OPTIONS) as ydl:
    #         try:
    #             info = ydl.extract_info(url, download=False)
    #         except:
    #             return False
    #     return {
    #         'link': 'https://www.youtube.com/watch?v=' + url,
    #         'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
    #         'source': info['formats'][0]['url'],
    #         'title': info['title']
    #     }
    
    # # Searches youtube for query. Returns list of videos.
    # def search_YT(self, search):
    #     queryString = parse.urlencode({'search_query': search})
    #     htmlContent = request.urlopen('http://www.youtube.com/results?' + queryString)
    #     searchResults = re.findall(
    #         '/watch\?v=(.{11})', htmlContent.read().decode())
    #     return searchResults[0:10]
    
    # def play_next(self, interaction):
    #     id = int(interaction.guild.id)
        
    #     # If not playing return
    #     if not self.is_playing[id]:
    #         return
        
    #     # If there is a next song play it.
    #     if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
    #         self.is_playing[id] = True
    #         self.queueIndex[id] += 1

    #         song = self.musicQueue[id][self.queueIndex[id]][0]
    #         message = self.now_playing_embed(interaction, song)
    #         coro = interaction.response.send_message(embed=message)
    #         fut = run_coroutine_threadsafe(coro, self.bot.loop)
    #         try:
    #             fut.result()
    #         except:
    #             pass
            

    #         self.vc[id].play(discord.FFmpegPCMAudio(
    #             song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(interaction))
    #     # No song to play
    #     else:
    #         self.queueIndex[id] += 1
    #         self.is_playing[id] = False

    # async def play_music(self, interaction):
    #     id = int(interaction.guild.id)
    #     if self.queueIndex[id] < len(self.musicQueue[id]):
    #         self.is_playing[id] = True
    #         self.is_paused[id] = False

    #         await self.join_VC(interaction, self.musicQueue[id][self.queueIndex[id]][1])

    #         song = self.musicQueue[id][self.queueIndex[id]][0]
    #         message = self.now_playing_embed(interaction, song)
    #         await interaction.response.send_message(embed=message)

    #         self.vc[id].play(discord.FFmpegPCMAudio(
    #             song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(interaction))
    #     else:
    #         await interaction.response.send_message("There are no songs in the queue to be played.")
    #         self.queueIndex[id] += 1
    #         self.is_playing[id] = False
    
    # @discord.app_commands.command(name="play", description="Plays a song from a search string.")
    # async def play(self, interaction, args: str):
    #     search = " ".join(args)
    #     id = int(interaction.guild.id)
    #     try:
    #         userChannel = interaction.user.voice.channel
    #     except:
    #         await interaction.response.send_message("You must be connected to a voice channel.")
    #         return
    #     if not args:
    #         if len(self.musicQueue[id]) == 0:
    #             await interaction.response.send_message("There are no songs to be played in the queue.")
    #             return
    #         elif not self.is_playing[id]:
    #             if self.musicQueue[id] == None or self.vc[id] == None:
    #                 await self.play_music(interaction)
    #             else:
    #                 self.is_paused[id] = False
    #                 self.is_playing[id] = True
    #                 self.vc[id].resume()
    #         else:
    #             return
    #     else:
    #         song = self.extract_YT(self.search_YT(search)[0])
    #         if type(song) == type(True):
    #             await interaction.response.send_message("Could not download the song. Incorrect format, try some different keywords.")
    #         else:
    #             self.musicQueue[id].append([song, userChannel])

    #             if not self.is_playing[id]:
    #                 await self.play_music(interaction)
    #             else:
    #                 message = self.added_song_embed(interaction, song)
    #                 await interaction.reponse.send_message(embed=message)
    
    # @discord.app_commands.command(name="add", description="Adds a song to the bot's song queue.")
    # async def add(self, interaction, args: str):
    #     search = " ".join(args)
    #     try:
    #         userChannel = interaction.message.author.voice.channel
    #     except:
    #         await interaction.response.send_message("You must be in a voice channel.")
    #         return
    #     if not args:
    #         await interaction.reponse.send_message("You need to specify a song to be added.")
    #     else:
    #         song = self.extract_YT(self.search_YT(search)[0])
    #         if type(song) == type(False):
    #             await interaction.response.send_message("Could not download the song. Incorrect format, try different keywords.")
    #             return
    #         else:
    #             self.musicQueue[interaction.guild.id].append([song, userChannel])
    #             message = self.added_song_embed(interaction, song)
    #             await interaction.response.send_message(embed=message)
    
    # @discord.app_commands.command(name="remove", description="Removes the last song from the song queue.")
    # async def remove(self, interaction):
    #     id = int(interaction.guild.id)
    #     if self.musicQueue[id] != []:
    #         song = self.musicQueue[id][-1][0]
    #         removeSongEmbed = self.removed_song_embed(interaction, song)
    #         await interaction.response.send_message(embed=removeSongEmbed)
    #     else:
    #         await interaction.reponse.send_message("There are no songs to be removed in the queue.")
    #     self.musicQueue[id] = self.musicQueue[id][:-1]
    #     if self.musicQueue[id] == []:
    #         if self.vc[id] != None and self.is_playing[id]:
    #             self.is_playing[id] = self.is_paused[id] = False
    #             await self.vc[id].disconnect()
    #             self.vc[id] = None
    #         self.queueIndex[id] = 0
    #     elif self.queueIndex[id] == len(self.musicQueue[id]) and self.vc[id] != None and self.vc[id]:
    #         self.vc[id].pause()
    #         self.queueIndex[id] -= 1
    #         await self.play_music(interaction)

    # @discord.app_commands.command(name="queue", description="Displays the current song queue.")
    # async def queue(self, interaction):
    #     id = int(interaction.guild.id)
    #     returnValue = ""
    #     if self.musicQueue[id] == []:
    #         await interaction.response.send_message("There are no songs in the queue.")
    #         return

    #     for i in range(self.queueIndex[id], len(self.musicQueue[id])):
    #         upNextSongs = len(self.musicQueue[id]) - self.queueIndex[id]
    #         if i > 5 + upNextSongs:
    #             break
    #         returnIndex = i - self.queueIndex[id]
    #         if returnIndex == 0:
    #             returnIndex = "Playing"
    #         elif returnIndex == 1:
    #             returnIndex = "Next"
    #         returnValue += f"{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})\n"

    #         if returnValue == "":
    #             await interaction.reponse.send_message("There are no songs in the queue.")
    #             return

    #     queue = discord.Embed(
    #         title="Current Queue",
    #         description=returnValue,
    #         colour=self.embedGreen
    #     )
    #     await interaction.response.send_message(embed=queue)

    # @discord.app_commands.command(name="pause", description="Pauses the current song.")
    # async def pause(self, interaction):
    #     id = int(interaction.guild.id)
    #     if not self.vc[id]:
    #         await interaction.response.send_message("There is no audio to be paused at the moment.")
    #     elif self.is_playing[id]:
    #         await interaction.response.send_message("Audio paused!")
    #         self.is_playing[id] = False
    #         self.is_paused[id] = True
    #         self.vc[id].pause()   
    
    # @discord.app_commands.command(name="resume", description="Resumes the current song.")
    # async def resume(self, interaction):
    #     id = int(interaction.guild.id)
    #     if not self.vc[id]:
    #         await interaction.reponse.send_message("There is no audio to be played at the moment.")
    #     elif self.is_paused[id]:
    #         await interaction.response.send_message("The audio is now playing!")
    #         self.is_playing[id] = True
    #         self.is_paused[id] = False
    #         self.vc[id].resume()    

    # @discord.app_commands.command(name="skip", description="Skips to the next song in queue.")
    # async def skip(self, interaction):
    #     id = int(interaction.guild.id)
    #     if self.vc[id] == None:
    #         await interaction.response.send_message("You need to be in a VC to use this command.")
    #     elif self.queueIndex[id] >= len(self.musicQueue[id]) - 1:
    #         await interaction.response.send_message("There is no next song in the queue. Replaying current song.")
    #         self.vc[id].pause()
    #         await self.play_music(interaction)
    #     elif self.vc[id] != None and self.vc[id]:
    #         self.vc[id].pause()
    #         self.queueIndex[id] += 1
    #         await self.play_music(interaction)
    
    # @discord.app_commands.command(name="previous", description="Goes back to the previous song in queue.") 
    # async def previous(self, interaction):
    #     id = int(interaction.guild.id)
    #     if self.vc[id] == None:
    #         await interaction.response.send_message("You need to be in a VC to use this command.")
    #     elif self.queueIndex[id] <= 0:
    #         await interaction.reponse.send_message("There is no previous song in the queue. Replaying current song.")
    #         self.vc[id].pause()
    #         await self.play_music(ctx)
    #     elif self.vc[id] != None and self.vc[id]:
    #         self.vc[id].pause()
    #         self.queueIndex[id] -= 1
    #         await self.play_music(ctx)

    # @discord.app_commands.command(name="clear", description="Clears the music queue.")
    # async def clear(self, interaction):
    #     id = int(interaction.guild.id)
    #     if self.vc[id] != None and self.is_playing[id]:
    #         self.is_playing = self.is_paused = False
    #         self.vc[id].stop()
    #     if self.musicQueue[id] != []:
    #         await interaction.send("The music queue has been cleared.")
    #         self.musicQueue[id] = []
    #     self.queueIndex = 0

    # @discord.app_commands.command(name="join", description="Joins the current voice channel.")
    # async def join(self, interaction):
    #     if interaction.user.voice:
    #         userChannel = interaction.user.voice.channel
    #         await self.join_VC(interaction, userChannel)
    #         await interaction.response.send_message(f'Bot has joined {userChannel}')
    #     else:
    #         await interaction.response.send_message("You need to be connected to a voice channel.")

    # @discord.app_commands.command(name="leave", description="Leaves the current voice channel.")
    # async def leave(self, interaction):
    #     id = int(interaction.guild.id)
    #     self.is_playing[id] = self.is_paused[id] = False
    #     self.musicQueue[id] = []
    #     self.queueIndex[id] = 0
    #     if self.vc[id] != None:
    #         await interaction.response.send_message("bot has left the chat")
    #         await self.vc[id].disconnect()
    #         self.vc[id] = None