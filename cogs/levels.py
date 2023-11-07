from discord.ext import commands
import discord
import sqlite3
import datetime

# Experience required per level (EXPERIENCE_MULTIPLIER * level)
EXPERIENCE_MULTIPLIER = 20
# Experience gained per message
MESSAGE_EXPERIENCE = 5


class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot, dbConnection: sqlite3.Connection):
        self.bot = bot
        self.connection = dbConnection
        print("Levels DB Connection Established")

    def __del__(self):
        print("Levels DB Connection Closed.")
        self.connection.close()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levels cog is ready.")
        self._initDatabase()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = int(member.guild.id)
        member_id = int(member.id)
        self.connection.execute(
            "INSERT OR IGNORE INTO levels (guild_id, user_id, user_name, experience, current_lvl) VALUES (?, ?, ?, ?, ?)", (guild_id, member_id, member.name, 0, 0))
        self.connection.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = int(member.guild.id)
        member_id = int(member.id)
        self.connection.execute(
            "DELETE FROM levels WHERE guild_id = ? AND user_id = ?", (guild_id, member_id))
        self.connection.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        guild_id = int(message.guild.id)
        member_id = int(message.author.id)
        experience = self._getExperience(guild_id, member_id)
        level = self._getLevel(guild_id, member_id)
        newExperience = experience + MESSAGE_EXPERIENCE
        if newExperience >= level*EXPERIENCE_MULTIPLIER:
            newLevel = level + 1
            self._setLevel(guild_id, member_id, newLevel)
            self._setExperience(guild_id, member_id, 0)
            await message.channel.send(f"{message.author.mention} has leveled up to level {newLevel}!")
        else:
            self._setExperience(guild_id, member_id, newExperience)

    def _initDatabase(self):
        self.connection.execute("""CREATE TABLE IF NOT EXISTS LEVELS (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        experience INTEGER NOT NULL,
        current_lvl INTEGER NOT NULL,
        UNIQUE(guild_id, user_id));""")

        guilds = self.bot.guilds
        for guild in guilds:
            for member in guild.members:
                self.connection.execute(
                    "INSERT OR IGNORE INTO levels (guild_id, user_id, user_name, experience, current_lvl) VALUES (?, ?, ?, ?, ?)", (guild.id, member.id, member.name, 0, 0))
        self.connection.commit()

    def _getExperience(self, guild_id, user_id):
        cursor = self.connection.execute(
            "SELECT experience FROM levels WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        experience = cursor.fetchone()[0]
        return experience

    def _getLevel(self, guild_id, user_id):
        cursor = self.connection.execute(
            "SELECT current_lvl FROM levels WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        current_lvl = cursor.fetchone()[0]
        return current_lvl

    def _setExperience(self, guild_id, user_id, newExperience):
        self.connection.execute(
            "UPDATE levels SET experience = ? WHERE user_id = ? AND guild_id = ?", (newExperience, user_id, guild_id))
        self.connection.commit()

    def _setLevel(self, guild_id, user_id, newLevel):
        self.connection.execute(
            "UPDATE levels SET current_lvl = ? WHERE user_id = ? AND guild_id = ?", (newLevel, user_id, guild_id))
        self.connection.commit()

    @discord.app_commands.command(name="level", description="Shows your current level.")
    async def level(self, interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        level = self._getLevel(guild_id, user_id)
        curExperience = self._getExperience(guild_id, user_id)
        if level == None:
            await interaction.response.send_message("Error getting your level.")
        else:
            embed = discord.Embed(title="Level", color=discord.Colour.green(
            ), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Level", value=level)
            embed.add_field(
                name="Experience", value=f"{curExperience}/{level*EXPERIENCE_MULTIPLIER}")
            embed.set_thumbnail(url=interaction.user.avatar)
            await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="lvlboard", description="Shows the top 10 users on the server.")
    async def lvlboard(self, interaction):
        guild_id = interaction.guild.id
        cursor = self.connection.execute(
            "SELECT user_name, experience, current_lvl FROM levels WHERE guild_id = ? ORDER BY experience DESC LIMIT 10", (guild_id,))
        rows = cursor.fetchall()
        embed = discord.Embed(title="Leaderboard", color=discord.Colour.green(
        ), timestamp=datetime.datetime.utcnow())
        for row in rows:
            embed.add_field(
                name=row[0], value=f"Level: {row[2]}\nExperience: {row[1]}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="rank", description="Shows your rank on the server.")
    async def rank(self, interaction):
        guild_id = interaction.guild.id
        cursor = self.connection.execute(
            "SELECT user_name, experience, current_lvl FROM levels WHERE guild_id = ? ORDER BY experience DESC", (guild_id,))
        rows = cursor.fetchall()
        embed = discord.Embed(title="Rank", color=discord.Colour.green(
        ), timestamp=datetime.datetime.utcnow())
        rank = 1
        for row in rows:
            if row[0] == interaction.user.name:
                break
            rank += 1
        embed.add_field(
            name="Rank", value=rank)
        await interaction.response.send_message(embed=embed)
