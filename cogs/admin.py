from discord.ext import commands
import discord
import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog is ready.")

    @discord.app_commands.command(name="shutdown", description="Shuts down the bot.")
    async def shutdown(self, ctx):
        print("Shutting Down...")
        await self.bot.close()

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
    
    # @commands.command()
    # async def ban(self, ctx, member, reason):
    #     try:
    #         await ctx.guild.ban(member, reason=reason)  
    #     except:
    #         await ctx.send("Could not ban user.")