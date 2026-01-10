import discord
from discord import ui, Interaction
from config import ADMIN_ROLE_ID, TICKET_CATEGORY_ID, ADMIN_GET_ROLE, DONE_CATEGORY_ID

# ================== ボタン ==================
class TicketDeleteButton(ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="チケット削除")
    async def callback(self, interaction: Interaction):
        await interaction.channel.delete()

class TicketCloseButton(ui.Button):
    def __init__(self, user: discord.Member):
        super().__init__(style=discord.ButtonStyle.secondary, label="対応済み")
        self.user = user
    async def callback(self, interaction: Interaction):
        await interaction.channel.set_permissions(self.user, send_messages=False)
        done = interaction.guild.get_channel(DONE_CATEGORY_ID)
        if done:
            await interaction.channel.edit(category=done)
        await interaction.response.send_message("対応済みにしました", ephemeral=True)

class TicketView(ui.View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton(user))
        self.add_item(TicketDeleteButton())

# ================== セレクト ==================
class TicketPanelSelect(ui.Select):
    def __init__(self, user: discord.Member):
        options = [
            discord.SelectOption(label="ゲーム"),
            discord.SelectOption(label="アカウント"),
            discord.SelectOption(label="その他")
        ]
        super().__init__(placeholder="チケットの種類を選択", options=options, min_values=1, max_values=1)
        self.user = user

    async def callback(self, interaction: Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(name=f"🎫｜{self.user.name}", overwrites=overwrites)
        embed = discord.Embed(
            title=f"Ticket | {self.user.name}",
            description=f"**種別:** {self.values[0]}\n管理者の対応をお待ちください。",
            color=discord.Color.blue()
        )
        notify_role = interaction.guild.get_role(ADMIN_GET_ROLE)
        content = self.user.mention
        if notify_role:
            content += f" {notify_role.mention}"

        await ch.send(content, embed=embed, view=TicketView(self.user))
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

# ================== パネルボタン ==================
class TicketPanelButton(ui.Button):
    def __init__(self):
        super().__init__(label="チケット作成", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: Interaction):
        view = ui.View()
        view.add_item(TicketPanelSelect(interaction.user))
        await interaction.response.send_message(
            "下記のセレクトメニューからチケットの種類を選択してください。",
            view=view,
            ephemeral=True
        )

# ================== パネル ==================
class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketPanelButton())

# ================== コマンド ==================
async def setup(bot):
    @bot.tree.command(name="ticket_panel")
    async def ticket_panel(interaction: Interaction):
        embed = discord.Embed(
            description="## __Ticket Panel__\n> 購入：お問い合わせ\n> 迷惑行為禁止",
            color=discord.Color.dark_grey()
        )
        await interaction.response.send_message(embed=embed, view=TicketPanel())
