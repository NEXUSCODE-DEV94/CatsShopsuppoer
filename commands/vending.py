import discord
from discord.ext import commands
import json
import os
import re
import datetime
from config import *

async def update_all_stats(bot):
    for channel_id in TARGET_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if not channel: continue
        try:
            count = 0
            async for _ in channel.history(limit=None):
                count += 1
            current_name = channel.name
            if "《" in current_name and "》" in current_name:
                new_name = re.sub(r"《.*?》", f"《{count}》", current_name)
                if current_name != new_name:
                    await channel.edit(name=new_name)
        except:
            pass

class CancelModal(discord.ui.Modal, title='キャンセル理由の入力'):
    reason = discord.ui.TextInput(
        label='キャンセル理由',
        style=discord.TextStyle.paragraph,
        placeholder='理由を入力してください',
        required=True
    )

    def __init__(self, buyer_id, item_name, admin_msg):
        super().__init__()
        self.buyer_id = buyer_id
        self.item_name = item_name
        self.admin_msg = admin_msg

    async def on_submit(self, interaction: discord.Interaction):
        try:
            buyer = await interaction.client.fetch_user(self.buyer_id)
            embed = discord.Embed(title="注文キャンセルのお知らせ", color=discord.Color.red())
            embed.description = f"注文がキャンセルされました。\n\n**商品名:** {self.item_name}\n**理由:** {self.reason.value}"
            await buyer.send(embed=embed)
            new_embed = self.admin_msg.embeds[0]
            new_embed.title = "【キャンセル済み】" + (new_embed.title or "")
            new_embed.color = discord.Color.default()
            await self.admin_msg.edit(embed=new_embed, view=None)
            await interaction.response.send_message("キャンセル処理が完了しました。", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"エラー: {e}", ephemeral=True)

class PayPayModal(discord.ui.Modal, title='PayPay決済'):
    paypay_link = discord.ui.TextInput(
        label='PayPayリンクを入力してください',
        placeholder='https://pay.paypay.ne.jp/...',
        min_length=20,
        max_length=41,
        required=True
    )

    def __init__(self, item_name, price, item_data):
        super().__init__()
        self.item_name = item_name
        self.price = price
        self.item_data = item_data

    async def on_submit(self, interaction: discord.Interaction):
        if not self.paypay_link.value.startswith("https://pay.paypay.ne.jp/"):
            await interaction.response.send_message("無効なリンクです。", ephemeral=True)
            return
        admin_channel = interaction.client.get_channel(ADMIN_LOG_CHANNEL_ID)
        if not admin_channel:
            await interaction.response.send_message("管理用チャンネルが見つかりません。", ephemeral=True)
            return
        embed = discord.Embed(title="購入リクエスト", color=discord.Color.green())
        embed.description = "送金金額を確認してください"
        embed.add_field(name="購入者", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
        embed.add_field(name="商品名", value=f"{self.item_name}", inline=True)
        embed.add_field(name="個数", value="1個", inline=True)
        embed.add_field(name="サーバー", value=f"{interaction.guild.name}", inline=True)
        embed.add_field(name="PayPayリンク", value=self.paypay_link.value, inline=False)
        now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M')
        embed.set_footer(text=now)
        view = AdminControlView()
        mention_text = f"<@&{MENTION_ROLE_ID}>" if MENTION_ROLE_ID else ""
        await admin_channel.send(content=mention_text, embed=embed, view=view)
        await interaction.response.send_message(embed=discord.Embed(description="購入をリクエストしました。", color=discord.Color.green()), ephemeral=True)

class AdminControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.is_received = False

    @discord.ui.button(label="受け取り完了", style=discord.ButtonStyle.green, custom_id="v_admin_receive")
    async def confirm_receive(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_received = True
        button.disabled = True
        button.label = "支払い受取済み"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="商品を配達", style=discord.ButtonStyle.blurple, custom_id="v_admin_deliver")
    async def deliver_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_received:
            await interaction.response.send_message("先に「受け取り完了」を押してください。", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        buyer_id = int(re.search(r"\((\d+)\)", embed.fields[0].value).group(1))
        item_name = embed.fields[1].value
        await interaction.response.defer(ephemeral=True)
        try:
            buyer = await interaction.client.fetch_user(buyer_id)
            now = datetime.datetime.now().strftime('%y/%m/%d %H:%M:%S')
            dm_embed = discord.Embed(title=f"{item_name}", color=discord.Color.green())
            dm_embed.description = f"購入日: {now}\n購入サーバー: {interaction.guild.name}"
            dm_embed.add_field(name="商品名", value=f"{item_name}", inline=False)
            dm_embed.add_field(name="個数", value="1個", inline=True)
            dm_view = discord.ui.View()
            dm_view.add_item(discord.ui.Button(label="サーバーへ移動する", url=INVITE_LINK, style=discord.ButtonStyle.link))
            await buyer.send(embed=dm_embed, view=dm_view)
            log_channel = interaction.client.get_channel(PURCHASE_LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(color=discord.Color.blue())
                log_embed.description = f"**商品購入ログ**\n商品: {item_name}\n個数: 1個\n購入者: {buyer.mention} ({buyer.id})"
                await log_channel.send(embed=log_embed)
                await update_all_stats(interaction.client)
            role = interaction.guild.get_role(CUSTOMER_ROLE_ID)
            member = interaction.guild.get_member(buyer_id)
            if role and member:
                await member.add_roles(role)
            new_embed = embed
            new_embed.title = "【配達完了】" + (new_embed.title or "")
            new_embed.color = discord.Color.blue()
            await interaction.message.edit(embed=new_embed, view=None)
            await interaction.followup.send("配達完了処理を行いました。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"エラー: {e}", ephemeral=True)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.danger, custom_id="v_admin_cancel")
    async def cancel_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        buyer_id = int(re.search(r"\((\d+)\)", embed.fields[0].value).group(1))
        item_name = embed.fields[1].value
        await interaction.response.send_modal(CancelModal(buyer_id, item_name, interaction.message))

class ConfirmView(discord.ui.View):
    def __init__(self, item_name, price, item_data):
        super().__init__(timeout=None)
        self.item_name = item_name
        self.price = price
        self.item_data = item_data

    @discord.ui.button(label="購入を確定", style=discord.ButtonStyle.green, custom_id="v_confirm_purchase")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PayPayModal(self.item_name, self.price, self.item_data))

class ItemSelectView(discord.ui.View):
    def __init__(self, items_dict):
        super().__init__(timeout=None)
        self.items_dict = items_dict
        options = []
        fixed_emoji = "<a:win11:1463441603057422419>"
        for name, data in items_dict.items():
            options.append(discord.SelectOption(label=name, description=f"価格: {data['price']}円", emoji=fixed_emoji))
        self.select = discord.ui.Select(placeholder="商品を選択してください", options=options, custom_id="v_item_select")
        self.select.callback = self.select_callback
        self.add_item(self.select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_name = self.select.values[0]
        item_data = self.items_dict[selected_name]
        price = item_data['price']
        embed = discord.Embed(title="購入確認", color=discord.Color.green())
        embed.description = f"**商品名:** {selected_name}\n**価格:** {price}円\n\nDMが解放されているか確認してください。"
        await interaction.response.send_message(embed=embed, view=ConfirmView(selected_name, price, item_data), ephemeral=True)

class VendingView(discord.ui.View):
    def __init__(self, items=None):
        super().__init__(timeout=None)
        self.items = items

    @discord.ui.button(label="購入", style=discord.ButtonStyle.green, custom_id="v_purchase_btn")
    async def purchase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.items is None:
            if os.path.exists("items.json"):
                with open("items.json", "r", encoding="utf-8") as f:
                    self.items = json.load(f)
        embed = discord.Embed(description="購入する商品を選択してください。", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, view=ItemSelectView(self.items), ephemeral=True)

async def setup(bot: commands.Bot):
    @bot.tree.command(name="r8-vending-panel", description="通常自販機パネルを設置します")
    async def vending_cmd(interaction: discord.Interaction):
        if not os.path.exists("items.json"):
            await interaction.response.send_message("items.jsonが見つかりません。", ephemeral=True)
            return
        with open("items.json", "r", encoding="utf-8") as f:
            items = json.load(f)
        
        await interaction.response.send_message("設置完了！", ephemeral=True)
        
        embed = discord.Embed(title="自販機パネル", description="商品を選択してください", color=discord.Color.green())
        for name, data in items.items():
            price = data.get("price", 0)
            embed.add_field(name=f"{name}", value=f"価格: {price}円", inline=False)
        
        await interaction.channel.send(embed=embed, view=VendingView(items))
