import discord
import random
from discord import ui, Interaction, app_commands
from config import VERIFY_ROLE_ID, EMOJI_ID, IMAGE_URL

class CalculationModal(ui.Modal):
    def __init__(self, role):
        super().__init__(title="Security Check")
        self.role = role
        
        self.num1 = random.randint(2, 9)
        self.num2 = random.randint(2, 9)
        self.answer = self.num1 * self.num2

        self.user_answer = ui.TextInput(
            label=f"問題: {self.num1} × {self.num2} は？",
            placeholder="答えを入力してください",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.user_answer)

    async def on_submit(self, interaction: Interaction):
        try:
            val = int(self.user_answer.value)
        except ValueError:
            embed = discord.Embed(title="Error", description="数字を入力してください。", color=discord.Color.red())
            embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if val != self.answer:
            embed = discord.Embed(title="Error", description="答えが間違っています。もう一度やり直してください。", color=discord.Color.red())
            embed.set_author(name="System", icon_url="https://i.postimg.cc/CxyfBNQ1/35112-error11.png")
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.user.add_roles(self.role)
        embed = discord.Embed(title="### Success", description="認証が完了しました。全てのコンテンツを利用可能です。", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="verify_button", emoji=EMOJI_ID)
    async def verify_button(self, interaction: Interaction, button: ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if role in interaction.user.roles:
            embed = discord.Embed(title="### Information", description="既に認証済みです。", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.send_modal(CalculationModal(role))

async def setup(bot):
    @bot.tree.command(name="verify", description="認証パネルを設置します")
    async def verify(interaction: Interaction):
        embed = discord.Embed(
            title="Member Verification", 
            description="### Click to Verify\n下のボタンを押して計算クイズに回答してください。\n\n認証後 [こちら](https://ptb.discord.com/channels/1313077923741438004/1313097431508058153) に同意したとみなします。", 
            color=discord.Color.from_rgb(43, 45, 49)
        )
        embed.set_image(url=IMAGE_URL)
        await interaction.channel.send(embed=embed, view=VerifyView())
        await interaction.response.send_message("Verification Panel Deployed", ephemeral=True)
