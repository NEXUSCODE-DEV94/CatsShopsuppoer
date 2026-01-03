import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
from aiohttp import web

# ================= 設定 =================
ADMIN_ROLE_ID = [1313086280141373441, 1452291945413083247]

TICKET_CATEGORY_ID = 1450086411956129894
YUZU_TICKET_CATEGORY_ID = 1455540840708702300
DONE_CATEGORY_ID = 1456845967545471157
LOG_CHANNEL_ID = 1313099999537532928

VERIFY_ROLE_ID = 1313100654507458561
EMOJI_ID = "<a:verify:1450459063052927079>"
IMAGE_URL = "https://i.postimg.cc/rmKMZkcy/standard.gif"
# =======================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

# ================= VERIFY =================
class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Verify",
        style=discord.ButtonStyle.primary,
        custom_id="verify_button",
        emoji=EMOJI_ID
    )
    async def verify_button(self, interaction: Interaction, button: ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)

        if role in interaction.user.roles:
            await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
            return

        await interaction.user.add_roles(role)
        await interaction.response.send_message("認証が完了しました", ephemeral=True)

# ================= 管理用ボタン =================
class TicketDeleteButton(ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.danger, label="チケット削除")

    async def callback(self, interaction: Interaction):
        await interaction.channel.delete()

class TicketCloseButton(ui.Button):
    def __init__(self, user: discord.Member):
        super().__init__(style=discord.ButtonStyle.secondary, label="管理者専用ボタン")
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

# ================= 通常チケット =================
class TicketSelect(ui.Select):
    def __init__(self, user: discord.Member):
        options = [
            discord.SelectOption(label="ゲーム", description="ゲーム関連の問い合わせ"),
            discord.SelectOption(label="アカウント", description="アカウント関連の問い合わせ"),
            discord.SelectOption(label="その他", description="その他の問い合わせ"),
        ]
        super().__init__(placeholder="チケットの種類を選択", options=options)
        self.user = user

    async def callback(self, interaction: Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(f"🎫｜{self.user.name}", overwrites=overwrites)

        embed = discord.Embed(
            title=f"Ticket | {self.user.name}",
            description=f"**種別:** {self.values[0]}\n管理者の対応をお待ちください。",
            color=discord.Color.blue()
        )

        await ch.send(self.user.mention, embed=embed, view=TicketView(self.user))
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="チケットを作成", style=discord.ButtonStyle.secondary, custom_id="create_ticket")
    async def create(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            "チケットの種類を選択してください",
            view=ui.View().add_item(TicketSelect(interaction.user)),
            ephemeral=True
        )

# ================= YUZU =================
class YuzuTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="チケットを作成", style=discord.ButtonStyle.secondary, custom_id="create_yuzu")
    async def create(self, interaction: Interaction, button: ui.Button):
        user = interaction.user
        category = interaction.guild.get_channel(YUZU_TICKET_CATEGORY_ID)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(f"🎫｜{user.name}", overwrites=overwrites)

        embed = discord.Embed(
            title=f"R18 Ticket | {user.name}",
            description="管理者の対応をお待ちください。",
            color=discord.Color.purple()
        )

        await ch.send(user.mention, embed=embed, view=TicketView(user))
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

# ================= コマンド =================
@bot.tree.command(name="verify")
async def verify(interaction: Interaction):
    await interaction.response.send_message("設置完了", ephemeral=True)
    embed = discord.Embed(
        title="Verification",
        description="下のボタンを押して認証してください。",
        color=discord.Color.blue()
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.channel.send(embed=embed, view=VerifyView())

@bot.tree.command(name="ticket_panel")
async def ticket_panel(interaction: Interaction):
    embed = discord.Embed(
        description="## __Ticket Panel__\n> 購入：お問い合わせ\n> 迷惑行為禁止",
        color=discord.Color.dark_grey()
    )
    await interaction.channel.send(embed=embed, view=TicketPanel())
    await interaction.response.send_message("設置完了", ephemeral=True)

@bot.tree.command(name="yuzu_ticket_panel")
async def yuzu_panel(interaction: Interaction):
    embed = discord.Embed(
        description="## R18用要望 / チケット\n> 支払い方法: PayPay, Kyash\n> 動画 ¥10 / 写真 ¥5",
        color=discord.Color.dark_grey()
    )
    await interaction.channel.send(embed=embed, view=YuzuTicketView())
    await interaction.response.send_message("設置完了", ephemeral=True)

# ================= 起動 =================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(TicketPanel())
    bot.add_view(YuzuTicketView())
    await bot.tree.sync()
    print("BOT READY")

async def start():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    await bot.start(TOKEN)

asyncio.run(start())


