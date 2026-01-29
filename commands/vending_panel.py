import discord
from discord import ui, Interaction, app_commands
from config import ITEMS, LOG_CHANNEL_ID

class VendingSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=item["name"], description=f"値段: {item['price']}円 | 在庫: {item['stock']}個", value=str(key)) 
            for key, item in ITEMS.items()
        ]
        super().__init__(placeholder="商品を選択してください", options=options, min_values=1, max_values=1, custom_id="vending_select_permanent")

    async def callback(self, interaction: Interaction):
        item_id = int(self.values[0])
        item = ITEMS[item_id]
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(title=f"無料配布: {item['name']}", color=discord.Color.green())
            embed.add_field(name="💎 商品名", value=item['name'], inline=False)
            embed.add_field(name="💰 価格", value=f"{item['price']}円", inline=False)
            embed.add_field(name="👤 購入者", value=interaction.user.mention, inline=False)
            embed.set_footer(text="developer @4bc6")
            await log_channel.send(embed=embed)

        dm_embed = discord.Embed(title="ご購入ありがとうございます", description=f"商品: {item['name']}\n{item['url']}", color=discord.Color.blue())
        try:
            await interaction.user.send(embed=dm_embed)
            await interaction.response.send_message("購入完了！DMを確認してください。", ephemeral=True)
        except:
            await interaction.response.send_message("DM送信失敗。設定を確認してください。", ephemeral=True)

class VendingView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🛒 購入", style=discord.ButtonStyle.green, custom_id="vending_buy_permanent")
    async def vending_buy(self, interaction: Interaction, button: ui.Button):
        view = ui.View()
        view.add_item(VendingSelect())
        await interaction.response.send_message("商品を選択してください。", view=view, ephemeral=True)

@app_commands.command(name="vending-panel", description="無料自販機パネルを設置します")
async def vending_panel_command(interaction: Interaction):
    items_text = "\n".join([f"**{item['name']}**" for item in ITEMS.values()])
    embed = discord.Embed(title="無料自販機", description=f"商品を選択してください\n\n{items_text}", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, view=VendingView())

async def setup(bot: discord.ext.commands.Bot):
    bot.tree.add_command(vending_panel_command)
