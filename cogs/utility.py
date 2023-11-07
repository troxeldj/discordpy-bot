from discord.ext import commands
import discord
import random
import datetime
import asyncio
import requests
from dotenv import load_dotenv
from os import getenv

load_dotenv()

WEATHER_API_KEY = getenv('WEATHER_API_KEY')


class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the Utility cog.

        Args:
            bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Called when the bot is ready.

        Prints a message to the console indicating that the Utility cog is ready.
        """
        print("Utility cog is ready.")

    @discord.app_commands.command(name="coinflip", description="Flips a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        """
        Flips a coin.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        randNum = random.randint(1, 10)
        if randNum <= 5:
            await interaction.response.send_message("Heads")
        else:
            await interaction.response.send_message("Tails")

    @discord.app_commands.command(name="roll", description="Rolls a dice.")
    async def roll(self, interaction: discord.Interaction, arg: int = 6) -> None:
        """
        Rolls a dice given a user specified number of sides.

        Args:
            interaction (discord.Interaction): The interaction object.
            arg (int, optional): The number of sides on the dice. Defaults to 6.
        """
        randNum = random.randint(1, int(arg))
        await interaction.response.send_message(randNum)

    @discord.app_commands.command(name="pick", description="Picks a random item from a list.")
    async def pick(self, interaction, args: str):
        args = args.split(" ")
        await interaction.response.send_message(random.choice(args))

    @discord.app_commands.command(name="math", description="Evaluates a math expression.")
    async def math(self, interaction: discord.Interaction, expression: str) -> None:
        """
        Evaluates a math expression.

        Args:
            interaction (discord.Interaction): The interaction object.
            expression (str): The math expression to evaluate.
        """
        isExpression = True
        for i in [*expression]:
            if str(i) not in ['+', '-', '*', '/', '%', '(', ')'] and not i.isdigit():
                isExpression = False

        if isExpression:
            try:
                calculated = eval(expression)
                await interaction.response.send_message(calculated)
            except:
                await interaction.response.send_message("Error occured. Please Check your expression.")
        else:
            await interaction.response.send_message("Not a valid math expression.")

    @discord.app_commands.command(name="userinfo", description="Displays information about a user.")
    async def userinfo(self, interaction, member: discord.Member = None) -> None:
        """
        Displays information about a user.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member, optional): The member to display information about. Defaults to None.
        """
        if member == None:
            member = interaction.user
        roles = [role for role in member.roles]
        embed = discord.Embed(title="User Info", description=f'Here\'s the user info for {member.name}', color=discord.Colour.green(
        ), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(
            name="Name", value=f'{member.name}#{member.discriminator}')
        embed.add_field(name="Nickname", value=member.display_name)
        embed.add_field(name="Status", value=member.status)
        embed.add_field(name="Created At", value=member.created_at.strftime(
            "%a, %B, %#d, %Y, %I:%M %p "))
        embed.add_field(name="Joined At", value=member.joined_at.strftime(
            "%a, %B, %#d, %Y, %I:%M %p "))
        embed.add_field(name=f'Roles({len(roles)})', value=" ".join(
            [role.mention for role in roles]))
        embed.add_field(name="Top Role", value=member.top_role)
        embed.add_field(name="Messages", value="0")
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="serverinfo", description="Displays information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        """
        Displays information about the current server.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        embed = discord.Embed(title="Server Info", description=f'Here\'s the server info for {interaction.guild.name}', color=discord.Colour.green(
        ), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(name="Description",
                        value=interaction.guild.description)
        embed.add_field(name="Members", value=interaction.guild.member_count)
        embed.add_field(
            name="Channels", value=f'{len(interaction.guild.text_channels)} text | {len(interaction.guild.voice_channels)} voice')
        embed.add_field(name="Roles", value=len(interaction.guild.roles))
        embed.add_field(name="Boosters",
                        value=interaction.guild.premium_subscription_count)
        embed.add_field(name="Created At", value=interaction.guild.created_at.strftime(
            "%a, %B, %#d, %Y, %I:%M %p "))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="remind", description="Reminds you of something.")
    async def reminder(self, interaction: discord.Interaction, time: str, *, reminder: str) -> None:
        """
        Reminds you of something after a specified amount of time.

        d = days
        h = hours
        m = minutes
        s = seconds

        Args:
            interaction (discord.Interaction): The interaction object.
            time (str): The amount of time to wait before reminding you.
            reminder (str): What to remind you about.
        """
        seconds = 0
        if reminder is None:
            await interaction.response.send_message("Please specify what do you want me to remind you about.")
            return
        if time.lower().endswith("d"):
            seconds += int(time[:-1]) * 60 * 60 * 24
            counter = f"{seconds // 60 // 60 // 24} days"
        if time.lower().endswith("h"):
            seconds += int(time[:-1]) * 60 * 60
            counter = f"{seconds // 60 // 60} hours"
        elif time.lower().endswith("m"):
            seconds += int(time[:-1]) * 60
            counter = f"{seconds // 60} minutes"
        elif time.lower().endswith("s"):
            seconds += int(time[:-1])
            counter = f"{seconds} seconds"
        if seconds == 0:
            await interaction.response.send_message("Please specify a proper duration.")
        elif seconds > 7776000:
            await interaction.response.send_message("You have specified a too long duration!\nMaximum duration is 90 days.")
        else:
            await interaction.response.send_message(f"Alright, I will remind you about {reminder} in {counter}.")
            await asyncio.sleep(seconds)
            await interaction.followup.send(f"Hi, you asked me to remind you about {reminder} {counter} ago.")

    @discord.app_commands.command(name="weather", description="Displays the weather.")
    async def weather(self, interaction: discord.Interaction, *, city: str):
        """
        Gets the current weather for a given city.

        Args:
            interaction (discord.Interaction): The interaction object.
            city (str): The city to get the weather for.
        """
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            main = data["main"]
            wind = data["wind"]
            weather = data["weather"][0]
            embed = discord.Embed(title=f"Weather in {data['name']}", color=discord.Colour.green(
            ), timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Description", value=weather["description"])
            embed.add_field(name="Temperature", value=f'{main["temp"]}°F')
            embed.add_field(name="Feels Like", value=f'{main["feels_like"]}°F')
            embed.add_field(name="Humidity", value=f'{main["humidity"]}%')
            embed.add_field(name="Wind Speed", value=f'{wind["speed"]} mph')
            embed.add_field(name="Cloudiness",
                            value=f'{data["clouds"]["all"]}%')
            embed.set_thumbnail(
                url=f'http://openweathermap.org/img/wn/{weather["icon"]}.png')
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Error finding weather.")

    @discord.app_commands.command(name="help", description="Displays the help menu.")
    async def help(self, interaction: discord.Interaction) -> None:
        """
        Displays the help menu.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        embed = discord.Embed(
            title="Help", description="Here's a list of commands.", color=discord.Colour.green())
        embed.add_field(name="/coinflip", value="Flips a coin.", inline=False)
        embed.add_field(name="/roll", value="Rolls a dice.", inline=False)
        embed.add_field(
            name="/pick", value="Picks a random item from a list.", inline=False)
        embed.add_field(
            name="/math", value="Evaluates a math expression.", inline=False)
        embed.add_field(
            name="/userinfo", value="Displays information about a user.", inline=False)
        embed.add_field(
            name="/serverinfo", value="Displays information about the server.", inline=False)
        embed.add_field(
            name="/remind", value="Reminds you of something.", inline=False)
        embed.add_field(
            name="/weather", value="Displays the weather given a city.", inline=False)
        embed.add_field(
            name="/play", value="Plays a song from yt link/playlist or query.", inline=False)
        embed.add_field(name="/pause", value="Pauses the song.", inline=False)
        embed.add_field(
            name="/resume", value="Resumes the song.", inline=False)
        embed.add_field(name="/stop", value="Stops the song.", inline=False)
        embed.add_field(
            name="/join", value="Joins the current voice channel.", inline=False)
        embed.add_field(
            name="/leave", value="Disconnects from the current voice channel.", inline=False)
        embed.add_field(name="/balance",
                        value="Displays your coin balance.", inline=False)
        embed.add_field(
            name="/queue", value="Displays the queue.", inline=False)
        embed.add_field(name="clear", value="Clears the queue.", inline=False)
        embed.add_field(
            name="/daily", value="Gives you your daily reward.", inline=False)
        embed.add_field(
            name="/gamble", value="Gambles your coins.", inline=False)
        embed.add_field(name="/leaderboard",
                        value="Displays the leaderboard.", inline=False)
        embed.add_field(name="/pay", value="Pays another user.", inline=False)
        embed.add_field(
            name="/level", value="Displays your level.", inline=False)
        embed.add_field(name="/lvlboard",
                        value="Displays the level leaderboard.", inline=False)
        embed.add_field(name="/announce (ADMIN ONLY)",
                        value="Announces a message to a channel.", inline=False)
        embed.add_field(name="/shutdown (ADMIN ONLY)",
                        value="Shuts down the bot.", inline=False)
        await interaction.response.send_message(embed=embed)
