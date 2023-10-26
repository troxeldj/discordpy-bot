import discord
from discord.ext import commands
import asyncio
from cogs import utility, admin, music
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.tree.sync()
    print("Slash Commands synced.")

async def main():
    await bot.add_cog(admin.Admin(bot))
    await bot.add_cog(utility.Utility(bot))
    await bot.add_cog(music.Music(bot))
    

asyncio.run(main())
bot.run(TOKEN)
