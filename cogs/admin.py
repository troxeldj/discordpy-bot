from discord.ext import commands
import discord
import datetime

class Admin(commands.Cog):
    def __init__(self, bot: discord.Interaction) -> None:
        """
        Initializes the Admin cog.

        Args:
            bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot

    async def is_admin(interaction: discord.Interaction) -> bool:
        """
        Checks if the user is an admin.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        if interaction.user.guild_permissions.administrator:
            return True
        else:
            await interaction.response.send_message("You do not have permission to use this command.")
            return False
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Runs when the cog is ready.
        
        prints a message when the cog is ready.


        """
        print("Admin cog is ready.")

    @discord.app_commands.command(name="shutdown", description="Shuts down the bot.")
    @discord.app_commands.check(is_admin)
    async def shutdown(self, interaction: discord.Interaction) -> None:
        """
        Shuts down the bot.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await interaction.response.send_message("Shutting down...")
        await self.bot.close()
    
    @discord.app_commands.command(name="announce", description="Announces a message to a channel.")
    @discord.app_commands.check(is_admin)
    async def announce(self, interaction: discord.Interaction, channel: str, message: str) -> None:
        """
        Announces a message to a channel.

        Args:
            interaction (discord.Interaction): The interaction object.
            channel (str): The channel to send the message to.
            message (str): The message to send.
        """
        channel = discord.utils.get(interaction.guild.channels, name=channel)
        if channel == None:
            await interaction.response.send_message("Channel not found.")
            return
        await channel.send(message)
        await interaction.response.send_message("Announcement sent.")                

    @discord.app_commands.command(name="kick", description="Kicks a user.")
    @discord.app_commands.check(is_admin)
    async def kick(self, interaction, member: discord.Member, reason: str) -> None:
        """
        Kicks a user from the server.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The member to kick.
            reason (str): The reason for kicking the member.
        """
        if member == None:
            await interaction.response.send_message("Member not found.")
            return
        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member} has been kicked.")

    @discord.app_commands.command(name="ban", description="Bans a user.")
    @discord.app_commands.check(is_admin)
    async def ban(self, interaction, member: discord.Member, reason: str) -> None:
        """
        Bans a user from the server.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The member to kick.
            reason (str): The reason for kicking the member.
        """
        if member == None:
            await interaction.response.send_message("Member not found.")
            return
        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member} has been banned.")

    @discord.app_commands.command(name="timeout", description="Timeouts a user.")
    @discord.app_commands.check(is_admin)
    async def timeout(self, interaction, member: discord.Member, duration: str) -> None:
        """
        Bans a user from the server.

        Args:
            interaction (discord.Interaction): The interaction object.
            member (discord.Member): The member to kick.
            duration (str): The duration of the timeout.
        """
        if member == None:
            await interaction.response.send_message("Member not found.")
            return
        if duration == None or duration.isnumeric() == False:
            await interaction.response.send_message("Invalid duration.")
            return
        duration = datetime.timedelta(seconds=int(duration))
        await member.timeout(duration)
        await interaction.response.send_message(f"{member} has been timed out for {duration} seconds.")
    
    # @commands.command()
    # async def ban(self, ctx, member, reason):
    #     try:
    #         await ctx.guild.ban(member, reason=reason)  
    #     except:
    #         await ctx.send("Could not ban user.")