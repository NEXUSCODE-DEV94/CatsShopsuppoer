import discord
from discord import ui, Interaction
from config import YUZU_TICKET_CATEGORY_ID, ADMIN_GET_ROLE, DONE_CATEGORY_ID

class YuzuTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="チケットを作成", style=discord.ButtonStyle.secondary, custom_id="create_yuzu")
    async def create(self, interaction: Interaction, button: ui.Button):
        user = interaction.user
        category = interaction.guild.get_channel(YUZU_TICKET_CATEGORY_ID)
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        role = interaction.guild.get_role(ADMIN_GET_ROLE)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch = await category.create_text_channel(name=f"🎫｜{user.name}", overwrites=overwrites)
        embed = discord.Embed(title=f"R18 Ticket | {user.name}", description="管理者の対応をお待ちください。", color=discord.Color.purple())
        await ch.send(f"{user.mention} {role.mention}", embed=embed, view=None)
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

async def setup(bot):
    @bot.tree.command(name="yuzu_ticket_panel")
    async def yuzu_panel(interaction: Interaction):
        embed = discord.Embed(description="## R18用要望 / チケット\n> 支払い方法: PayPay, Kyash\n> 動画 ¥10 / 写真 ¥5", color=discord.Color.dark_grey())
        await interaction.channel.send(embed=embed, view=YuzuTicketView())
        await interaction.response.send_message("設置完了", ephemeral=True)
