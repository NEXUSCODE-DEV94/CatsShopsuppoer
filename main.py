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
    nuke,
    google
)

from config import TOKEN

# ================= 設定 =================
GUILD_ID = 1313077923741438004

CHANNEL_IDS = [
    1363459327448584192,
    1457317342488035502
]

ERROR_NOTIFY_CHANNEL_ID = 1313099999537532928
MENTION_USER_ID = 1396695477411381308

# Discordの制限（10分に2回まで）を考慮し、短すぎない値を推奨
UPDATE_INTERVAL = 500
# ======================================

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

# ================= エラー通知 =================
async def notify_error(error: Exception):
    channel = bot.get_channel(ERROR_NOTIFY_CHANNEL_ID)
    if channel is None:
        return

    # 通常メッセージでメンション
    await channel.send(f"<@{MENTION_USER_ID}>")

    # 埋め込み
    embed_msg = discord.Embed(
        title="エラーが発生しました",
        description=f"```\n{error}\n```",
        color=0xFF0000
    )
    await channel.send(embed=embed_msg)

# ================= 自動更新タスク =================
@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_channel_names():
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild is None:
            raise RuntimeError("Guildが取得できません")

        for channel_id in CHANNEL_IDS:
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            # メッセージ数をカウント
            count = 0
            async for _ in channel.history(limit=None):
                count += 1

            # 【修正点】《 》の中の数字だけを置換する正規表現
            # 例: "在庫《101》個" -> "在庫《105》個"
            pattern = r"(?<=《)\d+(?=》)"
            
            if re.search(pattern, channel.name):
                # 既に 《数字》 がある場合は置換
                new_name = re.sub(pattern, str(count), channel.name)
            else:
                # 《数字》 が無い場合は末尾に付与（フォールバック）
                new_name = f"{channel.name}《{count}》"

            # チャンネル名が実際に変わる場合のみ編集を実行（API制限対策）
            if channel.name != new_name:
                await channel.edit(name=new_name)

    except Exception as e:
        await notify_error(e)

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

    # ヘルスチェック用のWebサーバー（Renderなどの維持用）
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

if __name__ == "__main__":
    asyncio.run(start())

