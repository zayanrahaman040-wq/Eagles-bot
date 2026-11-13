import discord
from discord.ext import commands
from discord import app_commands
import os, json

TOKEN = os.getenv("TOKEN")
CANALE_LOG_ID = 1570920876591808693  # Forum notifiche
FILE_WARN = "warn.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def carica_warn():
    try:
        with open(FILE_WARN, "r") as f: return json.load(f)
    except: return {}

def salva_warn(d):
    with open(FILE_WARN, "w") as f: json.dump(d, f, indent=4)

# --- MODAL PER MOTIVO ---
class MotivoModal(discord.ui.Modal, title="Motivo"):
    motivo = discord.ui.TextInput(label="Motivo", placeholder="Scrivi il motivo...", required=True, max_length=200)
    def __init__(self, azione, utente):
        super().__init__()
        self.azione = azione
        self.utente = utente
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        log_ch = guild.get_channel(CANALE_LOG_ID)
        if self.azione == "ban":
            try: await self.utente.send(f"🚫 Sei stato BANNATO da {guild.name}\nMotivo: {self.motivo.value}")
            except: pass
            await self.utente.ban(reason=str(self.motivo.value))
            colore, titolo = 0xFF0000, "🚫 BAN"
        else:
            warns = carica_warn()
            uid = str(self.utente.id)
            warns[uid] = warns.get(uid, 0) + 1
            salva_warn(warns)
            try: await self.utente.send(f"⚠️ Hai ricevuto un WARN in {guild.name}\nMotivo: {self.motivo.value}\nTotale warn: {warns[uid]}/3")
            except: pass
            colore, titolo = 0xF1C40F, f"⚠️ WARN - {warns[uid]}/3"
            if warns[uid] >= 3:
                await self.utente.ban(reason="3 warn")
                titolo = "🚫 BAN AUTOMATICO - 3 WARN"

        embed = discord.Embed(title=titolo, color=colore)
        embed.add_field(name="👤 Utente", value=f"{self.utente.mention} ({self.utente})", inline=False)
        embed.add_field(name="📝 Motivo", value=self.motivo.value, inline=False)
        embed.add_field(name="👮 Da", value=interaction.user.mention, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if log_ch:
            await log_ch.send(embed=embed)

# --- VIEW CON 2 BOTTONI ---
class PannelloView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🚫 BAN", style=discord.ButtonStyle.red, custom_id="btn_ban")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tagga l'utente da bannare:", ephemeral=True, view=SelezionaUtente("ban"))
    @discord.ui.button(label="⚠️ WARN", style=discord.ButtonStyle.blurple, custom_id="btn_warn")
    async def warn_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tagga l'utente da warnare:", ephemeral=True, view=SelezionaUtente("warn"))

class SelezionaUtente(discord.ui.View):
    def __init__(self, azione):
        super().__init__(timeout=60)
        self.azione = azione
    @discord.ui.user_select(placeholder="Seleziona utente...")
    async def seleziona(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        utente = select.values[0]
        membro = interaction.guild.get_member(utente.id)
        await interaction.response.send_modal(MotivoModal(self.azione, membro))

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(PannelloView())
    print(f"✅ ONLINE: {bot.user}")

@bot.tree.command(name="pannello", description="Crea pannello BAN / WARN")
async def pannello(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo Admin!", ephemeral=True); return
    embed = discord.Embed(title="🛡️ PANNELLO STAFF", description="Clicca un bottone per bannare o warnare!", color=0x2B6BFF)
    await interaction.response.send_message(embed=embed, view=PannelloView())

bot.run(TOKEN)
