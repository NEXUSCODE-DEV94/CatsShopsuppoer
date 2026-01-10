import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
from aiohttp import web
from datetime import datetime, timezone, timedelta
import re
import random
from discord.ext import tasks, commands

# ================= 設定 =================
ADMIN_ROLE_ID = [1313086280141373441, 1452291945413083247]

TICKET_CATEGORY_ID = 1450086411956129894
YUZU_TICKET_CATEGORY_ID = 1455540840708702300
DONE_CATEGORY_ID = 1456845967545471157
LOG_CHANNEL_ID = 1313099999537532928

VERIFY_ROLE_ID = 1313100654507458561
EMOJI_ID = "<a:verify:1450459063052927079>"
IMAGE_URL = "https://i.postimg.cc/rmKMZkcy/standard.gif"

GUILD_ID = 1313077923741438004
CHANNEL_ID = 1457317342488035502
UPDATE_INTERVAL = 300

LOG_CHANNEL_ID = 1457317342488035502

ITEMS = {
    1: {
        "name": "[🍿] Netflix, Amazon Prime 無料",
        "price": 0,
        "stock": 9999999999,
        "url": "https://net20.cc/login2"
    },
    2: {
        "name": "[📩]Gmail 無限",
        "price": 0,
        "stock": 9999999999,
        "url": "https://smailpro.com"
    },
    3: {
        "name": "[🚮]捨てアド",
        "price": 0,
        "stock": 9999999999,
        "url": """https://www.gmailnator.com
https://m.kuku.lu
https://sute.jp
https://dropmail.me"""
    },
    4: {
        "name": "[📱]TikTok 無料・ウォーターマークなしダウンロード",
        "price": 0,
        "stock": 9999999999,
        "url": "https://tiktokio.com/ja/"
    },
}

NUKE_GIFS = [
    "https://i.pinimg.com/originals/3a/e7/92/3ae792706e97941696b70b4763bd2963.gif",
    "https://i.pinimg.com/originals/08/b4/f3/08b4f35b31e0ea0948ca7b5778e32b54.gif",
    "https://i.pinimg.com/originals/58/70/72/587072da657dcee567164c2ff718e08e.gif",
    "https://i.pinimg.com/originals/b0/45/fc/b045fc647b6a4a4bc2dd3d31f4a948ef.gif",
    "https://i.pinimg.com/originals/6a/8e/4d/6a8e4d2b450f10d3733422efc4e95526.gif",
]

PATTERN_NORMAL = re.compile(r"^(.+?)・(.+)$")
PATTERN_QUOTED = re.compile(r"^『(.+?)』｜(.+)$")

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

        for ch in interaction.guild.text_channels:
            if ch.category_id == DONE_CATEGORY_ID:
                continue
            if ch.name == f"🎫｜{self.user.name}":
                await interaction.response.send_message(
                    f"すでにチケットがあります → {ch.mention}",
                    ephemeral=True
                )
                return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(
            f"🎫｜{self.user.name}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"Ticket | {self.user.name}",
            description=f"**種別:** {self.values[0]}\n管理者の対応をお待ちください。",
            color=discord.Color.blue()
        )

        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        await ch.send(
            f"{user.mention} {role.mention}",
            embed=embed,
            view=TicketView(user)
        )
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="チケットを作成", style=discord.ButtonStyle.secondary, custom_id="create_ticket")
    async def create(self, interaction: Interaction, button: ui.Button):
        view = ui.View()
        view.add_item(TicketSelect(interaction.user))
        await interaction.response.send_message(
            "チケットの種類を選択してください",
            view=view,
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

        for ch in interaction.guild.text_channels:
            if ch.category_id == DONE_CATEGORY_ID:
                continue
            if ch.name == f"🎫｜{self.user.name}":
                await interaction.response.send_message(
                    f"すでにチケットがあります → {ch.mention}",
                    ephemeral=True
                )
                return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await category.create_text_channel(
            f"🎫｜{user.name}",
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"R18 Ticket | {user.name}",
            description="管理者の対応をお待ちください。",
            color=discord.Color.purple()
        )

        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        await ch.send(
            f"{user.mention} {role.mention}",
            embed=embed,
            view=TicketView(user)
        )
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

# ================= コマンド =================
@bot.tree.command(name="verify")
async def verify(interaction: Interaction):
    embed = discord.Embed(
        title="Verification",
        description="下のボタンを押して認証してください。",
        color=discord.Color.blue()
    )
    embed.set_image(url=IMAGE_URL)
    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message("設置完了", ephemeral=True)

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

# ================= Embed コマンド =================
@bot.tree.command(name="embed", description="カスタムEmbedを送信します")
async def embed(
    interaction: discord.Interaction,
    title: str | None,
    description: str,
    view_dev: str
):
    try:
        desc = description.replace("\\n", "\n")
        embed = discord.Embed(
            title=title if title else None,
            description=desc,
            color=discord.Color.dark_grey()
        )

        JST = timezone(timedelta(hours=9))
        now = datetime.now(JST)

        if view_dev.lower() == "y":
            embed.set_footer(
                text=f"developer @4bc6・{now.strftime('%Y/%m/%d %H:%M')}",
                icon_url=interaction.user.display_avatar.url
            )

        await interaction.response.send_message("送信完了！！", ephemeral=True)
        await interaction.channel.send(embed=embed)

    except Exception as e:
        error_text = str(e)
        if len(error_text) > 1800:
            error_text = error_text[:1800] + "…"
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"エラーが発生しました\n```{error_text}```",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"エラーが発生しました\n```{error_text}```",
                ephemeral=True
            )

# ================= チャンネル名変更 =================
@bot.tree.command(name="name-change-1", description="サーバー内の全チャンネルを変更")
async def name_change_1(interaction: discord.Interaction):
    guild = interaction.guild
    changed = 0

    for channel in guild.text_channels:
        if "・" not in channel.name:
            continue
        match = PATTERN_NORMAL.match(channel.name)
        if not match:
            continue
        emoji, name = match.groups()
        new_name = f"『{emoji}』｜{name}"
        if channel.name == new_name:
            continue
        await channel.edit(name=new_name)
        changed += 1

    await interaction.response.send_message(f"変更完了：{changed} チャンネル", ephemeral=True)

@bot.tree.command(name="name-change-2", description="サーバー内の全チャンネル名を元に戻す")
async def name_change_2(interaction: discord.Interaction):
    guild = interaction.guild
    changed = 0

    for channel in guild.text_channels:
        match = PATTERN_QUOTED.match(channel.name)
        if not match:
            continue
        emoji, name = match.groups()
        new_name = f"{emoji}・{name}"
        await channel.edit(name=new_name)
        changed += 1

    await interaction.response.send_message(f"復元完了：{changed} チャンネル", ephemeral=True)

# ================= Nuke =================
@bot.tree.command(name="nuke", description="チャンネルを再生成するコマンド")
@app_commands.checks.has_permissions(manage_channels=True)
async def nuke(interaction: discord.Interaction):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("このコマンドはテキストチャンネルでのみ使用できます。", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    old_position = channel.position
    old_category = channel.category

    new_channel = await channel.clone(reason=f"Nuked by {interaction.user}", category=old_category)
    await new_channel.edit(position=old_position)
    await channel.delete(reason=f"Nuked by {interaction.user}")

    embed = discord.Embed(title="💥 Nuke", description="チャンネルを再生成しました。", color=discord.Color.red())
    embed.set_image(url=random.choice(NUKE_GIFS))
    await new_channel.send(embed=embed)

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("権限がありません。（チャンネル管理が必要）", ephemeral=True)
    else:
        raise error
# ================= Vending =================
# ================= Vending =================
class VendingSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=item["name"],
                description=f"値段: {item['price']}円 | 在庫: {item['stock']}個",
                value=str(key)
            ) for key, item in ITEMS.items()
        ]
        super().__init__(placeholder="商品を選択してください", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        item_id = int(self.values[0])
        item = ITEMS[item_id]

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            title=f"無料配布: {item['name']}",
            color=discord.Color.green()
        )
        embed.add_field(name="商品名", value=item['name'], inline=False)
        embed.add_field(name="価格", value=f"{item['price']}円", inline=False)
        embed.add_field(name="購入者", value=interaction.user.mention, inline=False)
        embed.add_field(name="数量", value="1個", inline=False)
        embed.set_footer(text="developer @4bc6")
        await log_channel.send(embed=embed)

        dm_embed = discord.Embed(
            title="ご購入ありがとうございます",
            description=f"商品: {item['name']}\n数量: 1\n以下の在庫をお受け取りください:\n{item['url']}",
            color=discord.Color.blue()
        )
        await interaction.user.send(embed=dm_embed)

        await interaction.response.send_message("購入完了！DMを確認してください。", ephemeral=True)


class VendingView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VendingButton())


class VendingButton(ui.Button):
    def __init__(self):
        super().__init__(label="購入", style=discord.ButtonStyle.green, custom_id="vending_buy")

    async def callback(self, interaction: Interaction):
        view = ui.View()
        view.add_item(VendingSelect())
        await interaction.response.send_message(
            "下記のセレクトメニューから商品を選択してください。",
            view=view,
            ephemeral=True
        )


@bot.tree.command(name="vending-panel", description="無料自販機パネルを設置します")
async def vending_panel(interaction: Interaction):
    embed = discord.Embed(
        title="無料自販機",
        description="下記ボタンを押して購入したい商品を選択してください\n\n" +
                    "\n".join([f"**{item['name']}**\n" for item in ITEMS.values()]),
        color=discord.Color.green()
    )

    embed.set_author(
        name="自販機パネル",
        icon_url="https://i.postimg.cc/9f11xvX1/18174-600x600-(1).jpg"
    )
    embed.set_footer(text="developer @4bc6")

    view = VendingView()
    await interaction.response.send_message(embed=embed, view=view)
# --aa-autokousinn--
@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_channel_name():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        return

    counter = 0
    async for _ in channel.history(limit=None):
        counter += 1

    new_name = f"『✅』｜配布実績《{counter}》"
    if channel.name != new_name:
        try:
            await channel.edit(name=new_name)
        except discord.HTTPException:
            print("チャンネル名更新でエラー発生（レート制限かも）")
# ============dmsendd====
@bot.tree.command(name="dm", description="指定ユーザーにDMを送信します")
@app_commands.describe(user="送信先ユーザー", message="送信するメッセージ")
async def dm(interaction: discord.Interaction, user: discord.User, message: str):
    """指定したユーザーにDMを送る"""
    try:
        embed = discord.Embed(
            title=f"{interaction.guild.name}オーナーからのDM",
            description=message,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"{interaction.user.name}")
        await user.send(embed=embed)
        await interaction.response.send_message(f"{user} にDMを送信しました。", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"DMの送信に失敗しました: {e}", ephemeral=True)
# ================= 起動 =================
@bot.event
async def on_ready():
    bot.add_view(VerifyView())
    bot.add_view(TicketPanel())
    bot.add_view(YuzuTicketView())
    bot.add_view(VendingView())
    await bot.tree.sync()
    update_channel_name.start()
    print("BOT READY")

async def start():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.environ.get("PORT", 10000))
    ).start()
    await bot.start(TOKEN)

asyncio.run(start())
