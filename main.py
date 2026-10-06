import os, discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread
import asyncio

# --- CONFIG ---
AUTO_ROLE_NOM = "Membre"
WELCOME_CHANNEL = "arrivees"  # nom de ton salon arrivees
LEAVE_CHANNEL = "departs"      # nom de ton salon departs
TOKEN = os.getenv("DISCORD_TOKEN")

ROLES_PANEL = {
    "Gamer": 0,
    "Otaku": 0,
    "Chill": 0,
    "Shinigami": 0
}
# Remplace les 0 par les vrais ID de tes rôles après

# --- KEEP ALIVE RENDER ---
app = Flask('')
@app.route('/')
def home(): return "SOUL BOT ON - Soul Society"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- SYSTEME ROLES BOUTONS ---
class RoleButton(discord.ui.Button):
    def __init__(self, label, role_id):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, custom_id=f"role:{role_id}")
        self.role_id = role_id
    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message("❌ Rôle introuvable, mets le bon ID dans ROLES_PANEL", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"➖ {role.name} retiré", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"➕ {role.name} ajouté", ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for name, rid in ROLES_PANEL.items():
            if rid != 0:
                self.add_item(RoleButton(name, rid))

@bot.event
async def on_ready():
    bot.add_view(RoleView())
    await bot.tree.sync()
    print(f"SOUL BOT CONNECTE - {bot.user}")

# --- WELCOME / LEAVE AUTO ---
@bot.event
async def on_member_join(member):
    # Auto-role
    role = discord.utils.get(member.guild.roles, name=AUTO_ROLE_NOM)
    if role:
        try: await member.add_roles(role)
        except: pass
    # Message arrivee
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL)
    if channel:
        embed = discord.Embed(title="Bienvenue dans la Soul Society ⚔️", description=f"Bienvenue {member.mention} ! Nous sommes maintenant **{member.guild.member_count}** !\nVa dans le panel des rôles !", color=0x9b59b6)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="SOUL BOT")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name=LEAVE_CHANNEL)
    if channel:
        embed = discord.Embed(description=f"**{member.name}** a quitté la Soul Society... On est plus que {member.guild.member_count} 😢", color=0xff0000)
        await channel.send(embed=embed)

# --- COMMANDES ---

@bot.tree.command(name="ping", description="Teste la latence")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong ! {round(bot.latency*1000)}ms ⚡")

@bot.tree.command(name="panel-roles", description="Affiche le panel de rôles")
@app_commands.checks.has_permissions(manage_roles=True)
async def panel_roles(interaction: discord.Interaction):
    embed = discord.Embed(title="🎭 SOUL BOT - Choisis tes rôles", description="Clique pour ajouter / retirer un rôle", color=0x2b2d31)
    await interaction.response.send_message(embed=embed, view=RoleView())

@bot.tree.command(name="embed", description="Crée un embed custom")
@app_commands.checks.has_permissions(manage_messages=True)
async def embed_cmd(interaction: discord.Interaction, titre: str, description: str, couleur: str = "#9b59b6"):
    try:
        color = discord.Color.from_str(couleur)
    except:
        color = discord.Color.purple()
    embed = discord.Embed(title=titre, description=description.replace("\\n", "\n"), color=color)
    embed.set_footer(text=f"Par {interaction.user.name}")
    await interaction.response.send_message("Embed envoyé ✅", ephemeral=True)
    await interaction.channel.send(embed=embed)

@bot.tree.command(name="bienvenue", description="Souhaite la bienvenue à quelqu'un")
async def bienvenue(interaction: discord.Interaction, membre: discord.Member):
    embed = discord.Embed(title="Bienvenue !", description=f"Tout le monde souhaite la bienvenue à {membre.mention} ! 🎉", color=0x9b59b6)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="say", description="Fais parler le bot")
@app_commands.checks.has_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Envoyé ✅", ephemeral=True)
    await interaction.channel.send(message.replace("\\n", "\n"))

@bot.tree.command(name="clear", description="Supprime des messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, nombre: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=nombre)
    await interaction.followup.send(f"✅ {len(deleted)} messages supprimés", ephemeral=True)

@bot.tree.command(name="ban", description="Ban un membre")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
    try:
        await membre.ban(reason=raison)
        await interaction.response.send_message(embed=discord.Embed(title="BAN 🔨", description=f"{membre} banni\nRaison: {raison}", color=0xff0000))
    except:
        await interaction.response.send_message("❌ Impossible (rôle trop haut)", ephemeral=True)

@bot.tree.command(name="unban", description="Deban un membre")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str, raison: str = "Pardonné"):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=raison)
        await interaction.response.send_message(f"✅ {user} déban")
    except:
        await interaction.response.send_message("❌ ID invalide ou pas banni", ephemeral=True)

@bot.tree.command(name="kick", description="Kick un membre")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune"):
    try:
        await membre.kick(reason=raison)
        await interaction.response.send_message(f"✅ {membre} kick - {raison}")
    except:
        await interaction.response.send_message("❌ Impossible", ephemeral=True)

@bot.tree.command(name="addrole", description="Donne un rôle")
@app_commands.checks.has_permissions(manage_roles=True)
async def addrole(interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
    await membre.add_roles(role)
    await interaction.response.send_message(f"✅ {role.mention} ajouté à {membre.mention}")

@bot.tree.command(name="removerole", description="Retire un rôle")
@app_commands.checks.has_permissions(manage_roles=True)
async def removerole(interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
    await membre.remove_roles(role)
    await interaction.response.send_message(f"✅ {role.mention} retiré de {membre.mention}")

keep_alive()
bot.run(TOKEN)
