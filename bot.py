import discord
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()
Discord_Token = os.getenv("DISCORDTOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --command ---------------------------------------------------------


@tree.command(name="ping", description="Test if bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)


@tree.command(name="login", description="Link your Riot account")
async def login(interaction: discord.Interaction, summoner_name: str, region: str):
    await interaction.response.send_message(
        f"Received: {summoner_name} on {region} — login logic coming soon!",
        ephemeral=True,
    )


@tree.command(name="recent", description="See your recent matches")
async def recent(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Fetching your recent matches — coming soon!", ephemeral=True
    )


# --StartUp -------------------------------------------------------
@client.event
async def on_ready():
    server_id = os.getenv("SERVER_ID")
    if server_id:
        try:
            guild = discord.Object(id=int(server_id))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f"Logged in as {client.user} (Synced to Guild ID: {server_id})")
        except ValueError:
            print(f"Error: SERVER_ID '{server_id}' is not a valid integer. Syncing globally instead.")
            await tree.sync()
            print(f"Logged in as {client.user} (Global Sync)")
    else:
        await tree.sync()
        print(f"Logged in as {client.user} (Global Sync)")


if Discord_Token:
    client.run(Discord_Token)
else:
    print("Error: DISCORDTOKEN not found in .env file.")

