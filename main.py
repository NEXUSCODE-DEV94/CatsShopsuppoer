import os
import discord
from discord.ext import commands
from typing import Optional
from keep_alive import keep_alive

# =====================
# 固定ID設定（ここだけ書き換え）
# =====================
ADMIN_ROLE_ID = 1313086280141373441      # 管理者ロールID
TICKET_CATEGORY_ID = 1450086411956129894# 未対応チケットカテゴリID
DONE_CATEGORY_ID = 1450086104182034512  # 対応済みカテゴリID
LOG_CHANNEL_ID = 1313099999537532928    # ログ送信先
STOCK_CHANNEL_ID = 1451850275592601731

TICKET_CUSTOM_ID = "ticket_open_button"

# =====================
# Bot設定
# =====================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.environ.get("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が環境変数に設定されていません")

# =====================
# チケット作成View（永続）
# =====================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="OPEN",
        style=discord.ButtonStyle.green,
        custom_id=TICKET_CUSTOM_ID
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        admin_role = guild.get_role(ADMIN_ROLE_ID)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        if not admin_role or not category:
            await interaction.response.send_message(
                "設定エラー：ロールまたはカテゴリが見つかりません。",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            f"🎫¦{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="チケット作成完了",
            description=f"{user.mention}\n\nこのチャンネルで内容を送信してください。",
            color=discord.Color.green()
        )

        await channel.send(
            embed=embed,
            view=AdminPanelView(user.id)
        )

        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    title="チケット作成",
                    description=f"作成者: {user.mention}\nチャンネル: {channel.mention}",
                    color=discord.Color.green()
                )
            )

        await interaction.response.send_message(
            f"{channel.mention} を作成しました。",
            ephemeral=True
        )

# =====================
# 管理者パネルView（永続）
# =====================
class AdminPanelView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        return role in interaction.user.roles if role else False

    @discord.ui.button(
        label="対応済み",
        style=discord.ButtonStyle.blurple,
        custom_id="ticket_done"
    )
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        owner = guild.get_member(self.owner_id)
        done_category = guild.get_channel(DONE_CATEGORY_ID)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        if owner:
            await channel.set_permissions(owner, send_messages=False)

        if done_category:
            await channel.edit(category=done_category)

        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    title="チケット対応済み",
                    description=f"チャンネル: {channel.mention}\n対応者: {interaction.user.mention}",
                    color=discord.Color.blurple()
                )
            )

        await interaction.response.send_message(
            "対応済みにしました。",
            ephemeral=True
        )

    @discord.ui.button(
        label="チケット削除",
        style=discord.ButtonStyle.red,
        custom_id="ticket_delete"
    )
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    title="チケット削除",
                    description=f"削除者: {interaction.user.mention}\nチャンネル: {interaction.channel.name}",
                    color=discord.Color.red()
                )
            )

        await interaction.response.send_message("チケットを削除します。", ephemeral=True)
        await interaction.channel.delete()

# =====================
# /ticket コマンド（設置専用）
# =====================
@bot.tree.command(name="ticket", description="チケットボタンを設置")
async def ticket(
    interaction: discord.Interaction,
    button_name: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None
):
    if description:
        description = description.replace("\\n", "\n")

    embed = discord.Embed(
        title=title or "チケット",
        description=description or "下のボタンからチケットを作成できます。",
        color=discord.Color.blurple()
    )

    if image_url:
        embed.set_image(url=image_url)

    view = TicketView()
    view.children[0].label = button_name

    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("設置完了", ephemeral=True)
# aa
@bot.tree.command(name="add-stock", description="在庫を追加して通知します")
async def add_stock(
    interaction: discord.Interaction,
    amount: int,
    product_name: str
):
    stock_channel = interaction.guild.get_channel(STOCK_CHANNEL_ID)

    if not stock_channel:
        await interaction.response.send_message(
            "在庫通知チャンネルが見つかりません。",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📦 在庫追加通知",
        color=discord.Color.green()
    )

    embed.add_field(
        name="🛒 商品名",
        value=product_name,
        inline=False
    )

    embed.add_field(
        name="📊 追加個数",
        value=f"**{amount} 個**",
        inline=False
    )

    embed.add_field(
        name="👤 実行者",
        value=interaction.user.mention,
        inline=False
    )

    embed.set_footer(text="Cats Shop Inventory System")
    embed.timestamp = discord.utils.utcnow()

    await stock_channel.send(embed=embed)

    await interaction.response.send_message(
        "在庫を追加しました。",
        ephemeral=True
    )

# =====================
# 起動時処理（超重要）
# =====================
@bot.event
async def on_ready():
    bot.add_view(TicketView())          # ← 永続チケットボタン
    bot.add_view(AdminPanelView(0))     # ← 永続管理ボタン
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.competing,
            name="Cats Shop🛒"
        )
    )
    await bot.tree.sync()
    print("BOT IS READY!!")

# =====================
# 実行
# =====================
keep_alive()
bot.run(TOKEN)
