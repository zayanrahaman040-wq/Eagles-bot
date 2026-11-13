import discord
from discord.ext import commands
import os, json

TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN") or next((v for k,v in os.environ.items() if k.startswith("DISCORD_")), None)
print("TOKEN TROVATO:", "SI" if TOKEN else "NO")
CANALE_LOG_ID = 1570920876591808693
FILE_WARN = "warn.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

def carica_warn():
    try:
        with open(FILE_WARN, "r") as f: return json.load(f)
    except: return {}
def salva_warn(d):
    with open(FILE_WARN, "w") as f: json.dump(d, f, indent=4)

class AzioneModal(discord.ui.Modal):
    def __init__(self, azione):
        super().__init__(title="BAN" if azione=="ban" else "WARN")
        self.azione = azione
        self.add_item(discord.ui.TextInput(label="ID Utente", placeholder="Copia ID utente", required=True, max_length=20))
        self.add_item(discord.ui.TextInput(label="Motivo", placeholder="Scrivi il motivo...", required=True, max_length=200))
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        try:
            user_id = int(self.children[0].value.strip())
            motivo = self.children[1].value
        except:
            await interaction.response.send_message("❌ ID non valido!", ephemeral=True); return
        membro = guild.get_member(user_id)
        if not membro:
            try: membro = await guild.fetch_member(user_id)
            except:
                await interaction.response.send_message("❌ Utente non trovato!", ephemeral=True); return
        log_ch = guild.get_channel(CANALE_LOG_ID)
        if self.azione == "ban":
            try: await membro.send(f"🚫 Sei stato BANNATO da {guild.name}\nMotivo: {motivo}")
            except: pass
            await membro.ban(reason=motivo)
            colore, titolo = 0xFF0000, "🚫 BAN"
        else:
            warns = carica_warn()
            uid = str(membro.id)
            warns[uid] = warns.get(uid, 0) + 1
            salva_warn(warns)
            try: await membro.send(f"⚠️ Hai ricevuto un WARN in {guild.name}\nMotivo: {motivo}\nTotale warn: {warns[uid]}/3")
            except: pass
            colore, titolo = 0xF1C40F, f"⚠️ WARN - {warns[uid]}/3"
            if warns[uid] >= 3:
                await membro.ban(reason="3 warn")
                titolo = "🚫 BAN AUTOMATICO - 3 WARN"
        embed = discord.Embed(title=titolo, color=colore)
        embed.add_field(name="👤 Utente", value=f"{membro.mention} ({membro})", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="👮 Da", value=interaction.user.mention, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        if log_ch:
            try: await log_ch.send(embed=embed)
            except: pass

class PannelloView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🚫 BAN", style=discord.ButtonStyle.red, custom_id="btn_ban")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AzioneModal("ban"))
    @discord.ui.button(label="⚠️ WARN", style=discord.ButtonStyle.blurple, custom_id="btn_warn")
    async def warn_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AzioneModal("warn"))

@bot.event
async def on_ready():
    bot.add_view(PannelloView())
    print(f"✅ ONLINE: {bot.user}")

@bot.command(name="pannello")
async def pannello(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Solo Admin!"); return
    embed = discord.Embed(title="🛡️ PANNELLO STAFF", description="Clicca un bottone!\n\n🚫 BAN = banna subito\n⚠️ WARN = 1 warn, a 3 warn = BAN auto", color=0x2B6BFF)
    await ctx.send(embed=embed, view=PannelloView())

bot.run(TOKEN)
