import discord
from discord.ext import commands
import asyncio
from cogs import utility, admin, music, economy, levels
from dotenv import load_dotenv
from os import getenv
import sqlite3

load_dotenv()

TOKEN = getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
dbConnection = sqlite3.connect('database.db')


@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.tree.sync()
    print("Slash Commands synced.")


async def main():
    await bot.add_cog(admin.Admin(bot))
    await bot.add_cog(utility.Utility(bot))
    await bot.add_cog(music.Music(bot))
    await bot.add_cog(economy.Economy(bot, dbConnection))
    await bot.add_cog(levels.Levels(bot, dbConnection))

asyncio.run(main())

bot.run(TOKEN)
