from discord.ext import commands
import discord
import sqlite3
import datetime
from random import randint

STARTING_BALANCE = 1000
DAILY_REWARD = 200


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = sqlite3.connect('economy.db')
        print("Econ DB Connection Established")

    def __del__(self):
        print("Econ DB Connection Closed.")
        self.connection.close()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Economy cog is ready.")
        self._initDatabase()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        id = int(member.guild.id)
        self.connection.execute("INSERT OR IGNORE INTO economy (guild_id, user_id, user_name, balance) VALUES (?, ?, ?, ?)",
                                (id, member.id, member.name, STARTING_BALANCE))
        self.connection.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild_id = int(member.guild.id)
        self.connection.execute(
            "DELETE FROM economy WHERE guild_id = ? AND user_id = ?", (guild_id, member.id))
        self.connection.commit()

    def _initDatabase(self):
        self.connection.execute("""CREATE TABLE IF NOT EXISTS ECONOMY (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        balance INTEGER NOT NULL,
        last_daily DATE,
        UNIQUE(guild_id, user_id));""")

        guilds = self.bot.guilds
        for guild in guilds:
            for member in guild.members:
                self.connection.execute("INSERT OR IGNORE INTO economy (guild_id, user_id, user_name, balance) VALUES (?, ?, ?, ?)", (
                    guild.id, member.id, member.name, STARTING_BALANCE))

        self.connection.commit()

    def _getBalance(self, guild_id, user_id):
        cursor = self.connection.execute(
            "SELECT balance FROM economy WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        balance = cursor.fetchone()[0]
        return balance

    def _setBalance(self, guild_id, user_id, newBalance):
        self.connection.execute(
            "UPDATE economy SET balance = ? WHERE user_id = ? AND guild_id = ?", (newBalance, user_id, guild_id))
        self.connection.commit()

    @discord.app_commands.command(name="balance", description="Shows your current coin balance.")
    async def balance(self, interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        balance = self._getBalance(guild_id, user_id)
        if balance == None:
            await interaction.response.send_message("Error fetching balance.")
            return
        embed = discord.Embed(title=f"{interaction.user.name}'s Balance", color=discord.Colour.green(
        ), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Balance", value=balance)
        embed.set_thumbnail(url=interaction.user.avatar)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="gamble", description="Gamble your coins away!")
    async def gamble(self, interaction, amount: str):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        balance = self._getBalance(guild_id, user_id)
        if not amount.isnumeric():  # Amount not a number
            await interaction.response.send_message("Invalid amount. Make sure it's a number.")
            return
        if balance == None:  # Error fetching balance
            await interaction.response.send_message("Error fetching balance.")
            return
        if int(amount) > balance or int(amount) <= 0:
            await interaction.response.send_message("You don't have enough coins.")
            return

        outcome = randint(0, 1)
        if outcome == 0:
            await interaction.response.send_message(f"You lost {amount} coins.")
            self._setBalance(guild_id, user_id, balance - int(amount))
        else:
            await interaction.response.send_message(f"You won {amount} coins.")
            self._setBalance(guild_id, user_id, balance + int(amount))

    @discord.app_commands.command(name="pay", description="Pay someone else.")
    async def pay(self, interaction, user: discord.User, amount: str):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        senderBalance = self._getBalance(guild_id, user_id)
        receiverBalance = self._getBalance(guild_id, user.id)
        if not amount.isnumeric():  # Amount not a number
            await interaction.response.send_message("Invalid amount. Make sure it's a number.")
            return
        if senderBalance == None:  # Error fetching balance
            await interaction.response.send_message("Error fetching balance.")
            return
        if int(amount) > senderBalance or int(amount) <= 0:
            await interaction.response.send_message("You don't have enough coins.")
            return

        self._setBalance(guild_id, user_id, senderBalance -
                         int(amount))  # Subtract from sender
        self._setBalance(guild_id, user.id, receiverBalance +
                         int(amount))  # Add to receiver
        await interaction.response.send_message(f"You paid {user.name} {amount} coins.")

    @discord.app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction):
        guild_id = interaction.guild.id
        user_id = interaction.user.id
        userBalance = self._getBalance(guild_id, user_id)

        cursor = self.connection.execute(
            "SELECT last_daily FROM economy WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        last_daily = cursor.fetchone()[0]
        last_daily = datetime.datetime.strptime(
            last_daily, "%Y-%m-%d").date() if last_daily != 'NULL' and last_daily is not None else None

        if last_daily == None:  # Never Collected Daily Reward
            self.connection.execute("UPDATE economy SET last_daily = ? WHERE user_id = ? AND guild_id = ?", (str(
                datetime.date.today()), user_id, guild_id))
            self.connection.commit()
            self._setBalance(guild_id, user_id, userBalance + DAILY_REWARD)
            await interaction.response.send_message(f"You claimed your daily reward of {DAILY_REWARD} coins.")
        else:
            if last_daily < datetime.date.today():  # Daily Reward claimed before today
                self.connection.execute("UPDATE economy SET last_daily = ? WHERE user_id = ? AND guild_id = ?", (str(
                    datetime.date.today()), user_id, guild_id))
                self.connection.commit()
                self._setBalance(guild_id, user_id, userBalance + DAILY_REWARD)
                await interaction.response.send_message(f"You claimed your daily reward of {DAILY_REWARD} coins.")
            elif last_daily == datetime.date.today():  # Daily Reward already claimed today
                await interaction.response.send_message("You already claimed your daily reward today.")
            else:  # Error of some sort
                self.connection.execute("UPDATE economy SET last_daily = ? WHERE user_id = ? AND guild_id = ?", (str(
                    datetime.date.today()), user_id, guild_id))
                await interaction.response.send_message("Error fetching last daily reward. Try again.")

    @discord.app_commands.command(name="leaderboard", description="Shows the top 10 richest people in the server.")
    async def leaderboard(self, interaction):
        guild_id = interaction.guild.id
        cursor = self.connection.execute(
            "SELECT user_name, balance FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT 10", (guild_id,))
        embed = discord.Embed(title=f"{interaction.guild.name}'s Leaderboard",
                              color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        for row in cursor:
            embed.add_field(name=row[0], value=row[1])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="beg", description="Beg for coins.")
    async def beg(self, interaction: discord.Interaction, member: discord.Member):
        if member == None:
            await interaction.response.send_message("Member not found.")
            return
        await interaction.response.send_message(f"{member.mention} has been begged for coins by {interaction.user.name}.")
