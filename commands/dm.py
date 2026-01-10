import discord
from discord import Interaction
from discord import app_commands

async def setup(bot):
    @bot.tree.command(name="dm", description="指定ユーザーにDMを送信します")
    @app_commands.describe(user="送信先ユーザー", message="送信するメッセージ")
    async def dm(interaction: Interaction, user: discord.User, message: str):
        try:
            embed = discord.Embed(title=f"{interaction.guild.name}オーナーからのDM", description=message, color=discord.Color.blue())
            embed.set_footer(text=f"Sended by {interaction.user.name}")
            await user.send(embed=embed)
            await interaction.response.send_message(f"{user} にDMを送信しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"DMの送信に失敗しました: {e}", ephemeral=True)
