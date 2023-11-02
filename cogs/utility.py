from discord.ext import commands
import discord
import random

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Utility cog is ready.")

    @discord.app_commands.command(name="coinflip", description="Flips a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        randNum = random.randint(1,10)
        if randNum <= 5:
            await interaction.response.send_message("Heads")
        else:
            await interaction.response.send_message("Tails")
    
    @discord.app_commands.command(name="roll", description="Rolls a dice.")
    async def roll(self, interaction: discord.Interaction, arg: int=6):
        randNum = random.randint(1, int(arg))
        await interaction.response.send_message(randNum)
    
    @discord.app_commands.command(name="pick", description="Picks a random item from a list.")
    async def pick(self, interaction, args: str):
        args = args.split(" ")
        await interaction.response.send_message(random.choice(args))

    @discord.app_commands.command(name="math", description="Evaluates a math expression.")
    async def math(self, interaction, expression:str):
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
    async def userinfo(self, interaction, member:discord.Member = None):
        if member == None:
            member = interaction.user
        roles = [role for role in member.roles]
        embed = discord.Embed(title="User Info", description=f'Here\'s the user info for {member.name}', color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=member.avatar)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Name", value=f'{member.name}#{member.discriminator}') 
        embed.add_field(name="Nickname", value=member.display_name)
        embed.add_field(name="Status", value=member.status)
        embed.add_field(name="Created At", value=member.created_at.strftime("%a, %B, %#d, %Y, %I:%M %p "))
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%a, %B, %#d, %Y, %I:%M %p "))
        embed.add_field(name=f'Roles({len(roles)})', value=" ".join([role.mention for role in roles]))
        embed.add_field(name="Top Role", value=member.top_role)
        embed.add_field(name="Messages", value="0")
        embed.add_field(name="Bot?", value="Yes" if member.bot else "No")
        await interaction.response.send_message(embed=embed)
    
    @discord.app_commands.command(name="serverinfo", description="Displays information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Server Info", description=f'Here\'s the server info for {interaction.guild.name}', color=discord.Colour.green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(name="Description", value=interaction.guild.description)
        embed.add_field(name="Members", value=interaction.guild.member_count)
        embed.add_field(name="Channels", value=f'{len(interaction.guild.text_channels)} text | {len(interaction.guild.voice_channels)} voice')
        embed.add_field(name="Roles", value=len(interaction.guild.roles))
        embed.add_field(name="Boosters", value=interaction.guild.premium_subscription_count)
        embed.add_field(name="Created At", value=interaction.guild.created_at.strftime("%a, %B, %#d, %Y, %I:%M %p "))
        await interaction.response.send_message(embed=embed)

    
    @discord.app_commands.command(name="help", description="Displays the help menu.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Help", description="Here's a list of commands.", color=discord.Colour.green())
        embed.add_field(name="/coinflip", value="Flips a coin.", inline=False)
        embed.add_field(name="/roll", value="Rolls a dice.", inline=False)
        embed.add_field(name="/pick", value="Picks a random item from a list.", inline=False)
        embed.add_field(name="/math", value="Evaluates a math expression.", inline=False)
        embed.add_field(name="/userinfo", value="Displays information about a user.", inline=False)
        embed.add_field(name="/serverinfo", value="Displays information about the server.", inline=False)
        embed.add_field(name="/play", value="Plays a song.", inline=False)
        embed.add_field(name="/pause", value="Pauses the song.", inline=False)
        embed.add_field(name="/resume", value="Resumes the song.", inline=False)
        embed.add_field(name="/stop", value="Stops the song.", inline=False)
        embed.add_field(name="/join", value="Joins the current voice channel.", inline=False)
        embed.add_field(name="/leave", value="Disconnects from the current voice channel.", inline=False)
        embed.add_field(name="/balance", value="Displays your coin balance.", inline=False)
        embed.add_field(name="/daily", value="Gives you your daily reward.", inline=False)
        embed.add_field(name="/gamble", value="Gambles your coins.", inline=False)
        embed.add_field(name="/leaderboard", value="Displays the leaderboard.", inline=False)
        embed.add_field(name="/pay", value="Pays another user.", inline=False)
        embed.add_field(name="/level", value="Displays your level.", inline=False)
        embed.add_field(name="/lvlboard", value="Displays the level leaderboard.", inline=False)
        embed.add_field(name="/announce (ADMIN ONLY)", value="Announces a message to a channel.", inline=False)
        embed.add_field(name="/shutdown (ADMIN ONLY)", value="Shuts down the bot.", inline=False)
        await interaction.response.send_message(embed=embed)