import os
import asyncio
import re
import logging
import discord
from discord import app_commands
from discord.ext import tasks, commands
from aiohttp import web
from commands import (
    verify,
    ticket_panel,
    yuzu_panel,
    vending_panel as vending_panel1, # 1. ここを変更
    embed,
    dm,
    name_change,
    nuke
)
from config import TOKEN

logging.basicConfig(level=logging.INFO)

GUILD_ID = 1313077923741438004
CHANNEL_IDS = [1363459327448584192, 1457317342488035502]
UPDATE_INTERVAL = 500

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--- ログイン成功: {bot.user} ---")
    
    bot.add_view(verify.VerifyView())
    bot.add_view(ticket_panel.TicketPanel())
    bot.add_view(ticket_panel.TicketView())
    bot.add_view(yuzu_panel.YuzuTicketView())
    bot.add_view(vending_panel1.VendingView()) # 修正後の変数名を使用
    print("Persistent Views added.")

    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"コマンド同期成功: {len(synced)}個のコマンドを同期しました")
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"コマンド同期エラー: {e}")

    if not update_channel_names.is_running():
        update_channel_names.start()

@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_channel_names():
    try:
        guild = bot.get_guild(GUILD_ID)
        if not guild: return
        for cid in CHANNEL_IDS:
            channel = guild.get_channel(cid)
            if not channel: continue
            count = 0
            async for _ in channel.history(limit=None): count += 1
            pattern = r"(?<=《)\d+(?=》)"
            if re.search(pattern, channel.name):
                new_name = re.sub(pattern, str(count), channel.name)
            else:
                new_name = f"{channel.name}《{count}》"
            if channel.name != new_name: await channel.edit(name=new_name)
    except Exception as e:
        print(f"Update Task Error: {e}")

async def start():
    cmd_modules = [
        ("verify", verify),
        ("ticket_panel", ticket_panel),
        ("yuzu_panel", yuzu_panel),
        ("vending_panel1", vending_panel1), # 2. ここを修正後の変数名に合わせる
        ("embed", embed),
        ("dm", dm),
        ("name_change", name_change),
        ("nuke", nuke)
    ]

    for name, mod in cmd_modules:
        try:
            await mod.setup(bot)
            print(f"モジュール読み込み成功: {name}")
        except Exception as e:
            print(f"モジュール読み込み失敗 [{name}]: {e}")
    
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start())
