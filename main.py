import os
import asyncio
import discord
from discord.ext import commands
from typing import Optional
from aiohttp import web
from discord import app_commands

ADMIN_ROLE_ID = [1313086280141373441, 1452291945413083247]

TICKET_CATEGORY_ID = 1450086411956129894
YUZU_TICKET_CATEGORY_ID = 1455540840708702300

DONE_CATEGORY_ID = 1450086104182034512
LOG_CHANNEL_ID = 1313099999537532928

TICKET_CUSTOM_ID = "ticket_open_button"
YUZU_TICKET_CUSTOM_ID = "yuzu_ticket_open_button"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が設定されていません")

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
                    color=discord.Color.blurple()
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
                    color=discord.Color.red()
                )
            )
        await interaction.response.send_message("削除します", ephemeral=True)
        await interaction.channel.delete()

class BaseTicketView(discord.ui.View):
    def __init__(self, button_label: str, category_id: int, custom_id: str):
        super().__init__(timeout=None)
        self.button_label = button_label
        self.category_id = category_id
        self.custom_id = custom_id

        self.add_item(
            discord.ui.Button(
                label=button_label,
                style=discord.ButtonStyle.green,
                custom_id=custom_id
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.type == discord.InteractionType.component:
        return

    if interaction.data.get("custom_id") not in [TICKET_CUSTOM_ID, YUZU_TICKET_CUSTOM_ID]:
        return

    guild = interaction.guild
    user = interaction.user
    custom_id = interaction.data["custom_id"]

    category_id = TICKET_CATEGORY_ID if custom_id == TICKET_CUSTOM_ID else YUZU_TICKET_CATEGORY_ID
    category = guild.get_channel(category_id)
    log_channel = guild.get_channel(LOG_CHANNEL_ID)

    if not category:
        await interaction.response.send_message("カテゴリが見つかりません", ephemeral=True)
        return

    admin_roles = [guild.get_role(rid) for rid in ADMIN_ROLE_ID if guild.get_role(rid)]

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
        description=f"{user.mention}\n\nこのチャンネルで内容を送信してください。",
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

@bot.tree.command(name="ticket", description="通常チケットパネルを設置")
@app_commands.describe(
    button_name="ボタン文字",
    image_url="画像URL"
)
async def ticket(
    interaction: discord.Interaction,
    button_name: str,
    image_url: Optional[str] = None
):
    embed = discord.Embed(
        description="__Ticket Panel__",
        color=discord.Color.blurple()
    )

    if image_url:
        embed.set_image(url=image_url)

    view = BaseTicketView(button_name, TICKET_CATEGORY_ID, TICKET_CUSTOM_ID)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("設置完了", ephemeral=True)

@bot.tree.command(name="yuzu_ticket", description="YUZU専用チケットパネルを設置")
@app_commands.describe(
    description="埋め込み説明文",
    image_url="画像URL"
)
async def yuzu_ticket(
    interaction: discord.Interaction,
    description: str,
    image_url: Optional[str] = None
):
    embed = discord.Embed(
        description=description,
        color=discord.Color.orange()
    )

    if image_url:
        embed.set_image(url=image_url)

    view = BaseTicketView("OPEN", YUZU_TICKET_CATEGORY_ID, YUZU_TICKET_CUSTOM_ID)
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("設置完了", ephemeral=True)

@bot.event
async def on_ready():
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
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(start_web_and_bot())
