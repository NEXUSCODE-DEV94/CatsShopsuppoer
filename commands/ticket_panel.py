import discord
from discord import ui, Interaction, app_commands
from config import ADMIN_ROLE_ID, TICKET_CATEGORY_ID, ADMIN_GET_ROLE, DONE_CATEGORY_ID

class TicketDeleteButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="チケット削除",
            custom_id="persistent:ticket_delete"
        )

    async def callback(self, interaction: Interaction):
        admin_role = interaction.guild.get_role(ADMIN_GET_ROLE)
        if admin_role not in interaction.user.roles:
            embed = discord.Embed(title="Error", description="権限がありません。", color=discord.Color.red())
            embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        await interaction.channel.delete()

class TicketCloseButton(ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="対応済み",
            custom_id="persistent:ticket_close"
        )

    async def callback(self, interaction: Interaction):
        admin_role = interaction.guild.get_role(ADMIN_GET_ROLE)
        if admin_role not in interaction.user.roles:
            embed = discord.Embed(title="Error", description="権限がありません。", color=discord.Color.red())
            embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        for target, overwrite in interaction.channel.overwrites.items():
            if isinstance(target, discord.Member):
                if not target.guild_permissions.administrator:
                    await interaction.channel.set_permissions(
                        target, 
                        view_channel=True,
                        send_messages=False, 
                        read_message_history=True
                    )
        
        done_category = interaction.guild.get_channel(DONE_CATEGORY_ID)
        if isinstance(done_category, discord.CategoryChannel):
            if len(done_category.channels) < 50:
                await interaction.channel.edit(category=done_category)
                await interaction.followup.send("対応済みに移動しました。", ephemeral=True)
            else:
                embed = discord.Embed(title="Error", description="対応済みカテゴリーが満杯です。手動で削除してください。", color=discord.Color.red())
                embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send("対応済み設定を完了しました（移動先カテゴリ未設定）。", ephemeral=True)

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton())
        self.add_item(TicketDeleteButton())

class TicketPanelSelect(ui.Select):
    def __init__(self, user: discord.Member):
        options = [
            discord.SelectOption(label="ゲーム", emoji="<:computer:1463159362922090539>"),
            discord.SelectOption(label="アカウント", emoji="<:user:1463159533353308224>"),
            discord.SelectOption(label="配布受け取り", emoji="<:present:1464785525880782918>"),
            discord.SelectOption(label="スロット購入", emoji="<:slots:1464787452219621500>"),
            discord.SelectOption(label="その他", emoji="<:mail:1463160014553350218>")
        ]
        super().__init__(
            placeholder="チケットの種類を選択",
            options=options,
            custom_id="persistent:ticket_select"
        )
        self.user = user

    async def callback(self, interaction: Interaction):
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category or len(category.channels) >= 50:
            embed = discord.Embed(title="Error", description="カテゴリーが見つからないか、満杯で作成できません。", color=discord.Color.red())
            embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        for rid in ADMIN_ROLE_ID:
            role = interaction.guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        
        ch = await category.create_text_channel(
            name=f"🎫｜{self.user.name}",
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title=f"Ticket | {self.user.name}",
            description=f"**種別:** {self.values[0]}\n管理者の対応をお待ちください。",
            color=discord.Color.blue()
        )
        
        notify_role = interaction.guild.get_role(ADMIN_GET_ROLE)
        content = self.user.mention
        if notify_role:
            content += f" {notify_role.mention}"
            
        await ch.send(content, embed=embed, view=TicketView())
        await interaction.response.send_message(f"{ch.mention} を作成しました", ephemeral=True)

class TicketPanelButton(ui.Button):
    def __init__(self):
        super().__init__(
            label="チケット作成",
            style=discord.ButtonStyle.primary,
            custom_id="persistent:ticket_create_trigger"
        )

    async def callback(self, interaction: Interaction):
        view = ui.View(timeout=60)
        view.add_item(TicketPanelSelect(interaction.user))
        await interaction.response.send_message("チケットの種類を選択してください。", view=view, ephemeral=True)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketPanelButton())

@app_commands.command(name="ticket_panel", description="チケットパネルを設置します")
async def ticket_panel_command(interaction: Interaction):
    embed = discord.Embed(
        description="## __Ticket Panel__\n> 購入：お問い合わせ\n> 迷惑行為禁止\n> 無言チケットは__BAN__対象です",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://i.postimg.cc/vB8mJrhs/catsshopticketgiggg.gif")
    await interaction.response.send_message(embed=embed, view=TicketPanel())

async def setup(bot):
    bot.tree.add_command(ticket_panel_command)
