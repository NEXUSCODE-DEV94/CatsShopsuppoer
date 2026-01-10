import discord
from discord import Interaction
from datetime import datetime, timezone, timedelta

async def setup(bot):
    @bot.tree.command(name="embed", description="カスタムEmbedを送信します")
    async def embed(interaction: Interaction, title: str | None, description: str, view_dev: str):
        try:
            desc = description.replace("\\n", "\n")
            embed = discord.Embed(title=title if title else None, description=desc, color=discord.Color.dark_grey())
            JST = timezone(timedelta(hours=9))
            now = datetime.now(JST)
            if view_dev.lower() == "y":
                embed.set_footer(text=f"developer @4bc6・{now.strftime('%Y/%m/%d %H:%M')}", icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message("送信完了！！", ephemeral=True)
            await interaction.channel.send(embed=embed)
        except Exception as e:
            error_text = str(e)[:1800] + "…" if len(str(e)) > 1800 else str(e)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"エラーが発生しました\n```{error_text}```", ephemeral=True)
            else:
                await interaction.followup.send(f"エラーが発生しました\n```{error_text}```", ephemeral=True)
