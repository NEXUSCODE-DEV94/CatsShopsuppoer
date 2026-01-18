import os
import asyncio
import re
import discord
from discord.ext import tasks, commands
from aiohttp import web

from commands import (
    verify,
    ticket_panel,
    yuzu_panel,
    vending_panel,
    embed,
    dm,
    name_change,
    nuke
)

from config import TOKEN

# ================= 設定 =================
GUILD_ID = 1313077923741438004

CHANNEL_IDS = [
    1363459327448584192,
    1457317342488035502
]

UPDATE_INTERVAL = 200

# ================= Intents =================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= Bot Ready =================
@bot.event
async def on_ready():
    bot.add_view(verify.VerifyView())
    bot.add_view(ticket_panel.TicketPanel())
    bot.add_view(yuzu_panel.YuzuTicketView())
    bot.add_view(vending_panel.VendingView())

    await bot.tree.sync()

    if not update_channel_names.is_running():
        update_channel_names.start()

    print(f"BOT READY : {bot.user}")

# ================= 自動更新タスク =================
@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_channel_names():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        print("guild取得失敗")
        return

    for channel_id in CHANNEL_IDS:
        channel = guild.get_channel(channel_id)
        if channel is None:
            print(f"channel取得失敗: {channel_id}")
            continue

        count = 0
        async for _ in channel.history(limit=None):
            count += 1

        new_name = re.sub(r"\d+", str(count), channel.name)

        if new_name == channel.name:
            new_name = f"{channel.name}{count}"

        if channel.name != new_name:
            try:
                await channel.edit(name=new_name)
                print(f"更新: {channel.name} → {new_name}")
            except discord.HTTPException as e:
                print(f"更新失敗 ({channel.id}): {e}")

@update_channel_names.before_loop
async def before_update_channel_names():
    await bot.wait_until_ready()

# ================= コマンド読み込み =================
async def load_all_commands():
    for cmd in [
        verify,
        ticket_panel,
        yuzu_panel,
        vending_panel,
        embed,
        dm,
        name_change,
        nuke
    ]:
        await cmd.setup(bot)

# ================= 起動処理 =================
async def start():
    await load_all_commands()

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
