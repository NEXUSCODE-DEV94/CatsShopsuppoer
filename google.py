import discord
from discord import app_commands
from discord.ext import commands
import urllib.parse

class GoogleSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="google-search", description="Googleで単語を検索するためのリンクを生成します")
    @app_commands.describe(word="検索したいワード")
    async def google_search(self, interaction: discord.Interaction, word: str):
        encoded_word = urllib.parse.quote(word)
        search_url = f"https://www.google.com/search?q={encoded_word}"

        embed = discord.Embed(
            title=f"🔍 「{word}」の検索結果",
            description=f"以下のリンクからGoogle検索結果を確認できます。\n\n**[ここをクリックして検索結果を表示]({search_url})**",
            color=0x4285F4
        )
        embed.set_footer(text="Google Search Link Generator")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GoogleSearch(bot))
