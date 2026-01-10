import discord
from discord import Interaction, app_commands
import random
from config import NUKE_GIFS

async def setup(bot):
    @bot.tree.command(name="nuke", description="チャンネルを再生成するコマンド")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def nuke(interaction: Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("このコマンドはテキストチャンネルでのみ使用できます。", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        old_position = channel.position
        old_category = channel.category
        new_channel = await channel.clone(reason=f"Nuked by {interaction.user}", category=old_category)
        await new_channel.edit(position=old_position)
        await channel.delete(reason=f"Nuked by {interaction.user}")
        embed = discord.Embed(title="💥 Nuke", description="チャンネルを再生成しました。", color=discord.Color.red())
        embed.set_image(url=random.choice(NUKE_GIFS))
        await new_channel.send(embed=embed)
