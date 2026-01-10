import discord
from discord import Interaction
import re

PATTERN_NORMAL = re.compile(r"^(.+?)・(.+)$")
PATTERN_QUOTED = re.compile(r"^『(.+?)』｜(.+)$")

async def setup(bot):
    @bot.tree.command(name="name-change-1", description="サーバー内の全チャンネルを変更")
    async def name_change_1(interaction: Interaction):
        guild = interaction.guild
        changed = 0
        for channel in guild.text_channels:
            if "・" not in channel.name:
                continue
            match = PATTERN_NORMAL.match(channel.name)
            if not match:
                continue
            emoji, name = match.groups()
            new_name = f"『{emoji}』｜{name}"
            if channel.name != new_name:
                await channel.edit(name=new_name)
                changed += 1
        await interaction.response.send_message(f"変更完了：{changed} チャンネル", ephemeral=True)

    @bot.tree.command(name="name-change-2", description="サーバー内の全チャンネル名を元に戻す")
    async def name_change_2(interaction: Interaction):
        guild = interaction.guild
        changed = 0
        for channel in guild.text_channels:
            match = PATTERN_QUOTED.match(channel.name)
            if not match:
                continue
            emoji, name = match.groups()
            new_name = f"{emoji}・{name}"
            await channel.edit(name=new_name)
            changed += 1
        await interaction.response.send_message(f"復元完了：{changed} チャンネル", ephemeral=True)
