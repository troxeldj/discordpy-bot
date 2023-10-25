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
                
        
