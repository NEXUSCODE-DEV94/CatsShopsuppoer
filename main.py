import os
import asyncio
import discord
from discord.ext import commands
from typing import Optional
from aiohttp import web

# =====================
# 固定ID設定
# =====================
ADMIN_ROLE_ID = [1313086280141373441, 1452291945413083247]
TICKET_CATEGORY_ID = 1450086411956129894
DONE_CATEGORY_ID = 1450086104182034512
LOG_CHANNEL_ID = 1313099999537532928
STOCK_CHANNEL_ID = 1451850275592601731

TICKET_CUSTOM_ID = "ticket_open_button"

# =====================
# Bot設定
# =====================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

# =====================
# 管理者パネル
# =====================
class AdminPanelView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return any(role.id in ADMIN_ROLE_ID for role in interaction.user.roles)

    @discord.ui.button(label="対応済み", style=discord.ButtonStyle.blurple, custom_id="ticket_done")
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
                    description=f"{channel.mention}\n{interaction.user.mention}",
                    color=discord.Color.blurple
                )
            )

        await interaction.response.send_message("対応済みにしました", ephemeral=True)

    @discord.ui.button(label="チケット削除", style=discord.ButtonStyle.red, custom_id="ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    description=f"{interaction.user.mention}\n{interaction.channel.name}",
                    color=discord.Color.red
                )
            )
        await interaction.response.send_message("削除します", ephemeral=True)
        await interaction.channel.delete()

# =====================
# チケット作成View
# =====================
class TicketView(discord.ui.View):
    def __init__(self, button_label: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label=button_label, style=discord.ButtonStyle.green, custom_id=TICKET_CUSTOM_ID))

    @discord.ui.button(custom_id=TICKET_CUSTOM_ID, style=discord.ButtonStyle.green, label="OPEN")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        admin_roles = [guild.get_role(rid) for rid in ADMIN_ROLE_ID if guild.get_role(rid)]

        if not category:
            await interaction.response.send_message("カテゴリが見つかりません", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        for role in admin_roles:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            f"🎫¦{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            description=f"{user.mention}\n\nこのチャンネルで内容を送信してください。\n迷惑行為禁止",
            color=discord.Color.green()
        )
        await channel.send(embed=embed, view=AdminPanelView(user.id))

        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    description=f"{user.mention}\n{channel.mention}",
                    color=discord.Color.green()
                )
            )

        await interaction.response.send_message(f"{channel.mention} を作成しました", ephemeral=True)

# =====================
# /ticket コマンド
# =====================
@bot.tree.command(name="ticket", description="チケットパネルを設置")
async def ticket(
    interaction: discord.Interaction,
    button_name: str,
    image_url: Optional[str] = None
):
    embed = discord.Embed(
        description="__Ticket Panel__\n> 購入 / お問い合わせ\n> 迷惑行為禁止",
        color=discord.Color.blurple
    )
    if image_url:
        embed.set_image(url=image_url)

    view = TicketView(button_label=button_name)
    msg = await interaction.channel.send(embed=embed, view=view)
    await msg.pin(reason="Ticket Panel")
    await interaction.response.send_message("設置完了", ephemeral=True)

# =====================
# 起動時
# =====================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("BOT READY")

# =====================
# Render用 Webサーバ＋Bot起動
# =====================
async def start_web_and_bot():
    # Webサーバ
    from aiohttp import web
    async def handle(request):
        return web.Response(text="Bot is running")

    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server running on port {port}")

    # Bot 起動
    await bot.start(TOKEN)

# =====================
# 起動
# =====================
if __name__ == "__main__":
    asyncio.run(start_web_and_bot())
