import discord
from discord import ui, Interaction
from config import VERIFY_ROLE_ID, EMOJI_ID, IMAGE_URL

class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verify", style=discord.ButtonStyle.primary, custom_id="verify_button", emoji=EMOJI_ID)
    async def verify_button(self, interaction: Interaction, button: ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        if role in interaction.user.roles:
            await interaction.response.send_message("すでに認証済みです。", ephemeral=True)
            return
        await interaction.user.add_roles(role)
        await interaction.response.send_message("認証が完了しました", ephemeral=True)

async def setup(bot):
    @bot.tree.command(name="verify")
    async def verify(interaction: Interaction):
        embed = discord.Embed(title="Verification", description="下のボタンを押して認証してください。", color=discord.Color.blue())
        embed.set_image(url=IMAGE_URL)
        await interaction.channel.send(embed=embed, view=VerifyView())
        await interaction.response.send_message("設置完了", ephemeral=True)
