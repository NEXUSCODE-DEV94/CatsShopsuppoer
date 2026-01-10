import os, asyncio, discord
from discord.ext import tasks, commands
from aiohttp import web
from commands import verify, ticket_panel, yuzu_panel, vending_panel, embed, dm, name_change, nuke
from config import TOKEN, GUILD_ID, CHANNEL_ID, UPDATE_INTERVAL

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Views の登録 ----------------
@bot.event
async def on_ready():
    bot.add_view(verify.VerifyView())
    bot.add_view(ticket_panel.TicketPanel())
    bot.add_view(yuzu_panel.YuzuTicketView())
    bot.add_view(vending_panel.VendingView())
    await bot.tree.sync()
    update_channel_name.start()
    print("BOT READY")

# ---------------- 自動更新 ----------------
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

# ---------------- コマンドセットアップ ----------------
async def load_all_commands():
    for cmd in [verify, ticket_panel, yuzu_panel, vending_panel, embed, dm, name_change, nuke]:
        await cmd.setup(bot)

async def start():
    await load_all_commands()
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    await bot.start(TOKEN)

asyncio.run(start())
