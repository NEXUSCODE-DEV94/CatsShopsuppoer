import discord
from discord import ui, Interaction
from config import ITEMS, LOG_CHANNEL_ID

class VendingSelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=item["name"], description=f"値段: {item['price']}円 | 在庫: {item['stock']}個", value=str(key)) for key, item in ITEMS.items()]
        super().__init__(placeholder="商品を選択してください", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: Interaction):
        item_id = int(self.values[0])
        item = ITEMS[item_id]
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(title=f"無料配布: {item['name']}", color=discord.Color.green())
        embed.add_field(name="商品名", value=item['name'], inline=False)
        embed.add_field(name="価格", value=f"{item['price']}円", inline=False)
        embed.add_field(name="購入者", value=interaction.user.mention, inline=False)
        embed.add_field(name="数量", value="1個", inline=False)
        embed.set_footer(text="developer @4bc6")
        await log_channel.send(embed=embed)

        dm_embed = discord.Embed(title="ご購入ありがとうございます", description=f"商品: {item['name']}\n数量: 1\n以下の在庫をお受け取りください:\n{item['url']}", color=discord.Color.blue())
        await interaction.user.send(embed=dm_embed)
        await interaction.response.send_message("購入完了！DMを確認してください。", ephemeral=True)

class VendingView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VendingButton())

class VendingButton(ui.Button):
    def __init__(self):
        super().__init__(label="購入", style=discord.ButtonStyle.green, custom_id="vending_buy")

    async def callback(self, interaction: Interaction):
        view = ui.View()
        view.add_item(VendingSelect())
        await interaction.response.send_message("下記のセレクトメニューから商品を選択してください。", view=view, ephemeral=True)

async def setup(bot):
    @bot.tree.command(name="vending-panel", description="無料自販機パネルを設置します")
    async def vending_panel(interaction: Interaction):
        embed = discord.Embed(title="無料自販機", description="下記ボタンを押して購入したい商品を選択してください\n\n" + "\n".join([f"**{item['name']}**\n" for item in ITEMS.values()]), color=discord.Color.green())
        embed.set_author(name="自販機パネル", icon_url="https://i.postimg.cc/9f11xvX1/18174-600x600-(1).jpg")
        embed.set_footer(text="developer @4bc6")
        await interaction.response.send_message(embed=embed, view=VendingView())
