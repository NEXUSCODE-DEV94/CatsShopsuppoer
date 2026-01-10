import asyncio
import discord
from discord.ext import commands, tasks
from aiohttp import web
from config import TOKEN, GUILD_ID, CHANNEL_ID, UPDATE_INTERVAL
import importlib
import os

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= 自動更新 =================
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

# ================= コマンド読み込み =================
command_files = [f.replace(".py", "") for f in os.listdir("./commands") if f.endswith(".py")]
for cmd in command_files:
    importlib.import_module(f"commands.{cmd}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    update_channel_name.start()
    print("BOT READY")

async def start():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    await bot.start(TOKEN)

asyncio.run(start())
