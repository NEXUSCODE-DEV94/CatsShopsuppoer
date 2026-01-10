import discord
from discord import ui, Interaction
from config import YUZU_TICKET_CATEGORY_ID, DONE_CATEGORY_ID

# 特定ユーザーID（固定）
SPECIAL_USER_ID = 1435193806503809095

class YuzuTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # 永続化

    @ui.button(label="チケットを作成", style=discord.ButtonStyle.secondary, custom_id="create_yuzu")
    async def create(self, interaction: Interaction, button: ui.Button):
        user = interaction.user
        category = interaction.guild.get_channel(YUZU_TICKET_CATEGORY_ID)

        # 権限設定
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        # 特定ユーザーにもアクセス権
        special_user = interaction.guild.get_member(SPECIAL_USER_ID)
        if special_user:
            overwrites[special_user] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # チャンネル作成
        ch = await category.create_text_channel(name=f"🎫｜{user.name}", overwrites=overwrites)

        embed = discord.Embed(
            title=f"R18 Ticket | {user.name}",
            description="<@1435193806503809095> の対応をお待ちください。",
            color=discord.Color.purple()
        )

        # メンションは作成者と特定ユーザーのみ
        mentions = user.mention
        if special_user:
            mentions += f" {special_user.mention}"

        await ch.send(content=mentions, embed=embed, view=None)

        # ephemeral で作成完了通知
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

# コマンド登録
async def setup(bot):
    @bot.tree.command(name="yuzu_ticket_panel")
    async def yuzu_panel(interaction: Interaction):
        embed = discord.Embed(
            description="## R18用要望 / チケット\n> 支払い方法: PayPay, Kyash\n> 動画 ¥10 / 写真 ¥5",
            color=discord.Color.dark_grey()
        )
        await interaction.channel.send(embed=embed, view=YuzuTicketView())
        await interaction.response.send_message("設置完了", ephemeral=True)
