import os
import discord
from discord.ext import commands
from typing import Optional
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.environ.get("DISCORD_TOKEN")

DONE_CATEGORY_ID = 1450086104182034512
LOG_CHANNEL_ID = 1313099999537532928

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="OPEN", style=discord.ButtonStyle.green, custom_id="ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        parts = interaction.data["custom_id"].split(":")
        if len(parts) != 3:
            await interaction.response.send_message("設定エラー", ephemeral=True)
            return

        _, admin_role_id, category_id = parts

        guild = interaction.guild
        user = interaction.user

        admin_role = guild.get_role(int(admin_role_id))
        category = guild.get_channel(int(category_id))
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            f"🎫¦{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="チケット作成完了",
            description=f"{user.mention}\n\nこのチャンネルで内容を送信してください。",
            color=discord.Color.green()
        )

        await channel.send(
            embed=embed,
            view=AdminPanelView(int(admin_role_id), user.id, DONE_CATEGORY_ID)
        )

        if log_channel:
            log = discord.Embed(
                title="チケット作成",
                description=f"作成者: {user.mention}\nチャンネル: {channel.mention}",
                color=discord.Color.green()
            )
            await log_channel.send(embed=log)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="チケットを作成しました",
                description=f"{channel.mention} を作成しました。",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class AdminPanelView(discord.ui.View):
    def __init__(self, admin_role_id: int, owner_id: int, done_category_id: int):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id
        self.owner_id = owner_id
        self.done_category_id = done_category_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        role = interaction.guild.get_role(self.admin_role_id)
        return role in interaction.user.roles if role else False

    @discord.ui.button(label="対応済み", style=discord.ButtonStyle.blurple, custom_id="ticket_done")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        owner = guild.get_member(self.owner_id)
        done_category = guild.get_channel(self.done_category_id)
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        if owner:
            await channel.set_permissions(owner, view_channel=True, send_messages=False)

        if done_category:
            await channel.edit(category=done_category)

        if log_channel:
            log = discord.Embed(
                title="チケット対応済み",
                description=f"チャンネル: {channel.mention}\n対応者: {interaction.user.mention}",
                color=discord.Color.blurple()
            )
            await log_channel.send(embed=log)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="対応済み",
                description="このチケットは対応済みとして処理されました。",
                color=discord.Color.blurple()
            )
        )

    @discord.ui.button(label="チケット削除", style=discord.ButtonStyle.red, custom_id="ticket_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        log_channel = guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:
            log = discord.Embed(
                title="チケット削除",
                description=f"削除者: {interaction.user.mention}\nチャンネル: {interaction.channel.name}",
                color=discord.Color.red()
            )
            await log_channel.send(embed=log)

        await interaction.response.send_message("チケットを削除します。", ephemeral=True)
        await interaction.channel.delete()

@bot.tree.command(name="ticket", description="チケットボタンを設置")
async def ticket(
    interaction: discord.Interaction,
    admin_role: discord.Role,
    category: discord.CategoryChannel,
    button_name: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    author_name: Optional[str] = None,
    author_icon_url: Optional[str] = None
):
    if description:
        description = description.replace("\\n", "\n")

    embed = discord.Embed(
        title=title or "チケット",
        description=description or "下のボタンからチケットを作成できます。",
        color=discord.Color.blurple()
    )

    if image_url:
        embed.set_image(url=image_url)

    if author_name:
        embed.set_author(
            name=author_name,
            icon_url=author_icon_url if author_icon_url else discord.Embed.Empty
        )

    view = TicketView()
    view.children[0].label = button_name
    view.children[0].custom_id = f"ticket:{admin_role.id}:{category.id}"

    await interaction.channel.send(embed=embed, view=view)

    await interaction.response.send_message(
        embed=discord.Embed(
            title="設置完了",
            description="チケットボタンを設置しました。",
            color=discord.Color.green()
        ),
        ephemeral=True
    )

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(AdminPanelView(0, 0, DONE_CATEGORY_ID))
    await bot.change_presence(
    activity=discord.Activity(
        type=discord.ActivityType.competing,
        name="Cats Shop🛒"
    )
)
    await bot.tree.sync()
    print("BOT IS READY!!")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN が環境変数に設定されていません")

keep_alive()
bot.run(TOKEN)