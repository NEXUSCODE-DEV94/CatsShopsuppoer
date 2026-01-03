import os
import asyncio
import discord
from discord.ext import commands
from typing import Optional
from aiohttp import web
from discord import app_commands

# ================= 設定 =================
ADMIN_ROLE_ID = [1313086280141373441, 1452291945413083247]

TICKET_CATEGORY_ID = 1450086411956129894
YUZU_TICKET_CATEGORY_ID = 1455540840708702300
DONE_CATEGORY_ID = 1456845967545471157
LOG_CHANNEL_ID = 1313099999537532928

VERIFY_ROLE_ID = 1313100654507458561
EMOJI_ID = "<a:verify:1450459063052927079>"
IMAGE_URL = "https://i.postimg.cc/rmKMZkcy/standard.gif"

TICKET_CUSTOM_ID = "ticket_open_button"
YUZU_TICKET_CUSTOM_ID = "yuzu_ticket_open_button"
# =======================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

# ================= 管理用 View =================
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

        if owner:
            await channel.set_permissions(owner, send_messages=False)

        done_category = guild.get_channel(DONE_CATEGORY_ID)
        if done_category:
            await channel.edit(category=done_category)

        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    description=f"{channel.mention}\n{interaction.user.mention}",
                    color=discord.Color.blurple()
                )
            )

        await interaction.response.send_message("対応済みにしました", ephemeral=True)

    @discord.ui.button(label="チケット削除", style=discord.ButtonStyle.secondary, custom_id="ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                embed=discord.Embed(
                    description=f"{interaction.user.mention}\n{interaction.channel.name}",
                    color=discord.Color.red()
                )
            )
        await interaction.response.send_message("削除します", ephemeral=True)
        await interaction.channel.delete()

# ================= チケット View =================
class BaseTicketView(discord.ui.View):
    def __init__(self, label: str, custom_id: str):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                custom_id=custom_id
            )
        )

# ================= 認証 View =================
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.primary,
        custom_id="verify_button",
        emoji=EMOJI_ID
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role is None:
            await interaction.response.send_message("ロールが見つかりません。", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message("認証が完了しました", ephemeral=True)

# ================= チケット作成処理 =================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    cid = interaction.data.get("custom_id")
    if cid not in [TICKET_CUSTOM_ID, YUZU_TICKET_CUSTOM_ID]:
        return

    guild = interaction.guild
    user = interaction.user
    category_id = TICKET_CATEGORY_ID if cid == TICKET_CUSTOM_ID else YUZU_TICKET_CATEGORY_ID
    category = guild.get_channel(category_id)

    if not category:
        await interaction.response.send_message("カテゴリが見つかりません", ephemeral=True)
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    for rid in ADMIN_ROLE_ID:
        role = guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    channel = await guild.create_text_channel(
        f"🎫¦{user.name}",
        category=category,
        overwrites=overwrites
    )

    await channel.send(
        embed=discord.Embed(
            description=f"{user.mention}\n\nこのチャンネルで内容を送信してください。",
            color=discord.Color.green()
        ),
        view=AdminPanelView(user.id)
    )

    await interaction.response.send_message(f"{channel.mention} を作成しました", ephemeral=True)

# ================= コマンド =================

@bot.tree.command(name="verify", description="認証パネルを送信")
@app_commands.checks.has_permissions(administrator=True)
async def verify(interaction: discord.Interaction):
    print(f"[VERIFY] 設置実行: {interaction.user} ({interaction.user.id})")
    await interaction.response.send_message("設置完了", ephemeral=True)

    embed = discord.Embed(
        title="Verification",
        description="下のボタンを押して認証してください。",
        color=discord.Color.blue()
    )
    embed.set_image(url=IMAGE_URL)

    await interaction.channel.send(embed=embed, view=VerifyView())

@bot.tree.command(name="ticket_panel", description="通常チケットパネルを設置")
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        description="## __Ticket Panel__\n> 購入：お問い合わせ\n> 迷惑行為禁止",
        color=discord.Color.dark_grey()
    )

    await interaction.channel.send(
        embed=embed,
        view=BaseTicketView("チケットを作成", TICKET_CUSTOM_ID)
    )
    await interaction.response.send_message("設置完了", ephemeral=True)

@bot.tree.command(name="yuzu_ticket_panel", description="YUZU専用チケットパネルを設置")
async def yuzu_ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        description=(
            "## 🔞 r18用要望 / チケット\n\n"
            "> 支払い方法: PayPay, Kyash\n"
            "> 動画 ¥10 / 写真 ¥5"
        ),
        color=discord.Color.dark_grey()
    )

    await interaction.channel.send(
        embed=embed,
        view=BaseTicketView("チケットを作成", YUZU_TICKET_CUSTOM_ID)
    )
    await interaction.response.send_message("設置完了", ephemeral=True)

# ================= 起動 =================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(BaseTicketView("dummy", TICKET_CUSTOM_ID))
    bot.add_view(BaseTicketView("dummy", YUZU_TICKET_CUSTOM_ID))
    await bot.tree.sync()
    print("BOT READY")

async def start_web_and_bot():
    async def handle(request):
        return web.Response(text="Bot is running")

    app = web.Application()
    app.router.add_get("/", handle)
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()

    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start_web_and_bot())
