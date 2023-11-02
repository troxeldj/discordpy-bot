from discord.ext import commands
import discord
import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_admin(interaction):
        if interaction.user.guild_permissions.administrator:
            return True
        else:
            await interaction.response.send_message("You do not have permission to use this command.")
            return False
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog is ready.")

    @discord.app_commands.command(name="shutdown", description="Shuts down the bot.")
    @discord.app_commands.check(is_admin)
    async def shutdown(self, interaction):
        await interaction.response.send_message("Shutting down...")
        await self.bot.close()
    
    @discord.app_commands.command(name="announce", description="Announces a message to a channel.")
    @discord.app_commands.check(is_admin)
    async def announce(self, interaction, channel: str, message: str):
        channel = discord.utils.get(interaction.guild.channels, name=channel)
        if channel == None:
            await interaction.response.send_message("Channel not found.")
            return
        await channel.send(message)
        await interaction.response.send_message("Announcement sent.")                
    
    # @commands.command()
    # async def ban(self, ctx, member, reason):
    #     try:
    #         await ctx.guild.ban(member, reason=reason)  
    #     except:
    #         await ctx.send("Could not ban user.")