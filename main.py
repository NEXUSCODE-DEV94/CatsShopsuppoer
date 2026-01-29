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
    vending_panel,
    embed,
    dm,
    name_change,
    nuke
)
from config import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

GUILD_ID = 1313077923741438004
CHANNEL_IDS = [1363459327448584192, 1457317342488035502]
UPDATE_INTERVAL = 500

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"Command Error: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"エラーが発生しました: {error}", ephemeral=True)

@bot.event
async def on_ready():
    bot.add_view(verify.VerifyView())
    bot.add_view(ticket_panel.TicketPanel())
    bot.add_view(ticket_panel.TicketView())
    bot.add_view(yuzu_panel.YuzuTicketView())
    bot.add_view(vending_panel.VendingView())

    print(f"Syncing commands for Guild ID: {GUILD_ID}...")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} commands.")

    if not update_channel_names.is_running():
        update_channel_names.start()

    print(f"--- BOT ONLINE: {bot.user} ---")

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
    for cmd in [verify, ticket_panel, yuzu_panel, vending_panel, embed, dm, name_change, nuke]:
        await cmd.setup(bot)
    
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Startup Error: {e}")
