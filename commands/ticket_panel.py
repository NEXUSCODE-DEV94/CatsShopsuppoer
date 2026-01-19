import discord
from discord import ui, Interaction
from config import ADMIN_ROLE_ID, TICKET_CATEGORY_ID, ADMIN_GET_ROLE, DONE_CATEGORY_ID

# ================== チケット内操作ボタン ==================
class TicketDeleteButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="チケット削除",
            custom_id="persistent:ticket_delete" # 永続化ID
        )

    async def callback(self, interaction: Interaction):
        # 削除権限の確認（必要に応じて追加）
        await interaction.channel.delete()

class TicketCloseButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="対応済み",
            custom_id="persistent:ticket_close" # 永続化ID
        )

    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # チャンネル内の一般ユーザーの送信権限を剥奪
        for target, overwrite in interaction.channel.overwrites.items():
            if isinstance(target, discord.Member):
                if not target.guild_permissions.administrator:
                    await interaction.channel.set_permissions(target, send_messages=False)

        # カテゴリ移動
        done = interaction.guild.get_channel(DONE_CATEGORY_ID)
        if done:
            await interaction.channel.edit(category=done)

        await interaction.followup.send("対応済みにしました（ユーザーの送信権限を停止しました）", ephemeral=True)

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # タイムアウトなし
        self.add_item(TicketCloseButton())
        self.add_item(TicketDeleteButton())

# ================== セレクトメニュー ==================
class TicketPanelSelect(ui.Select):
    def __init__(self, user: discord.Member):
        options = [
            discord.SelectOption(label="ゲーム", emoji="🎮"),
            discord.SelectOption(label="アカウント", emoji="👤"),
            discord.SelectOption(label="その他", emoji="❓")
        ]
        super().__init__(
            placeholder="チケットの種類を選択",
            options=options,
            custom_id="persistent:ticket_select"
        )
        self.user = user

    async def callback(self, interaction: Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            return await interaction.response.send_message("エラー: カテゴリが見つかりません", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(
            name=f"🎫｜{self.user.name}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"Ticket | {self.user.name}",
            description=f"**種別:** {self.values[0]}\n管理者の対応をお待ちください。",
            color=discord.Color.blue()
        )

        notify_role = interaction.guild.get_role(ADMIN_GET_ROLE)
        content = self.user.mention
        if notify_role:
            content += f" {notify_role.mention}"

        # チケットチャンネルにViewを送信（ここでもTicketViewを渡す）
        await ch.send(content, embed=embed, view=TicketView())
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

# ================== パネル（最初のボタン） ==================
class TicketPanelButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="チケット作成",
            style=discord.ButtonStyle.primary,
            custom_id="persistent:ticket_create_trigger" # 永続化ID
        )

    async def callback(self, interaction: Interaction):
        # セレクトメニューを表示（これ自体は一時的なViewでOK）
        view = ui.View(timeout=60)
        view.add_item(TicketPanelSelect(interaction.user))
        await interaction.response.send_message("チケットの種類を選択してください。", view=view, ephemeral=True)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketPanelButton())

async def setup(bot):
    # bot.add_view は main.py の on_ready で行うため、ここでは tree 登録のみ
    pass
