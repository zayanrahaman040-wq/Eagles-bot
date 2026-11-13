import discord, os, aiohttp
from discord.ext import commands
from discord.ui import View, Modal, TextInput

TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
FORUM_CHANNEL_ID = 1570920876591808693

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_roblox_info(username):
    async with aiohttp.ClientSession() as s:
        async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames":[username]}) as r:
            data = await r.json()
            if not data.get("data"): return None
            user = data["data"][0]
            uid = user["id"]
        async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false") as r:
            thumb = await r.json()
            avatar = thumb["data"][0]["imageUrl"]
            return user["name"], user["displayName"], avatar, f"https://www.roblox.com/users/{uid}/profile"

class BanWarnModal(Modal):
    def __init__(self, tipo):
        super().__init__(title=f"{tipo} - Giocatore Roblox")
        self.tipo = tipo
        self.nome = TextInput(label="Nome utente Roblox", placeholder="Es: xX_Eagle_Xx")
        self.motivo = TextInput(label="Motivo", placeholder="Es: Cheating / Insulti", style=discord.TextStyle.paragraph)
        self.add_item(self.nome)
        self.add_item(self.motivo)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        info = await get_roblox_info(str(self.nome.value).strip())
        if not info:
            await interaction.followup.send("❌ Nome Roblox non trovato!", ephemeral=True)
            return
        name, display, avatar, link = info
        forum = bot.get_channel(FORUM_CHANNEL_ID)
        if forum is None:
            await interaction.followup.send("❌ Canale forum non trovato!", ephemeral=True)
            return
        colore = discord.Color.red() if self.tipo=="BAN" else discord.Color.orange()
        embed = discord.Embed(title=f"{'🚫 BAN' if self.tipo=='BAN' else '⚠️ WARN'} - {display} (@{name})", description=f"**Motivo:** {self.motivo.value}\n**Staff:** {interaction.user.mention}\n**Profilo:** [Clicca qui]({link})", color=colore)
        embed.set_thumbnail(url=avatar)
        embed.set_image(url=avatar)
        await forum.create_thread(name=f"{self.tipo} - {name} - {self.motivo.value[:40]}", content="Nuova notifica staff", embed=embed)
        await interaction.followup.send(f"✅ Pubblicato nel forum! Faccia di **{name}** trovata!", ephemeral=True)

class Pannello(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🚫 BAN", style=discord.ButtonStyle.danger)
    async def ban(self, interaction, button): await interaction.response.send_modal(BanWarnModal("BAN"))
    @discord.ui.button(label="⚠️ WARN", style=discord.ButtonStyle.secondary)
    async def warn(self, interaction, button): await interaction.response.send_modal(BanWarnModal("WARN"))

@bot.event
async def on_ready():
    print(f"✅ ONLINE: {bot.user}")

@bot.command()
async def pannello(ctx):
    embed = discord.Embed(title="🛡️ PANNELLO STAFF", description="Clicca BAN o WARN, scrivi nome Roblox e motivo.\nIl bot manderà la faccia Roblox nel forum!", color=discord.Color.blue())
    await ctx.send(embed=embed, view=Pannello())

bot.run(TOKEN)
