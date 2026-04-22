from discord import app_commands
from discord.ext import commands
import aiohttp
import os

from database.db import get_user

RIOT_API_KEY = os.getenv("LEAGUEAPI")
REGION = "na1"

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Show your LoL rank, level, and win rate")
    async def profile(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral = False)
        
        # get user from the db
        discord_id = str(interaction.user.id)
        user = get_user(discord_id)

        #check if user login
        if not user:
            await interaction.followup.send(
                "❌ You haven't linked your Riot account yet. Use `/login` first."
            )
            return

        _, puuid, game_name, tag_line = user
        headers = {"X-Riot-Token": RIOT_API_KEY}
        
        async with aiohttp.ClientSession() as session:
            # 1. Get summoner data (level) via PUUID
            summoner = await fetch(
                session,
                f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}",
                headers
            )
            if not summoner:
                await interaction.followup.send("❌ Could not fetch summoner data.")
                return

            summoner_id = summoner["id"]
            level = summoner["summonerLevel"]

            # 2. Get rank & LP (League-v4)
            leagues = await fetch(
                session,
                f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}",
                headers
            )
        # Parse ranked solo queue data
        rank_info = get_solo_rank(leagues)

        # Build win rate
        wins = rank_info.get("wins", 0)
        losses = rank_info.get("losses", 0)
        total = wins + losses
        win_rate = f"{round(wins / total * 100)}%" if total > 0 else "N/A"

        # Build Discord embed
        embed = discord.Embed(
            title=f"📊 {game_name}#{tag_line}",
            color=0x1a78c2
        )
        embed.add_field(name="🎮 Level", value=str(level), inline=True)
        embed.add_field(
            name="🏆 Rank",
            value=format_rank(rank_info),
            inline=True
        )
        embed.add_field(name="📈 Win Rate", value=win_rate, inline=True)
        embed.add_field(
            name="📋 Record",
            value=f"{wins}W / {losses}L" if total > 0 else "Unranked",
            inline=True
        )
        embed.set_footer(text="Powered by Riot Games API")

        await interaction.followup.send(embed=embed)
# ── Helpers ────────────────────────────────────────────────────────────────────
#try to get the information
async def fetch(session:aiohttp.ClientSession, url: str, headers: dict):
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return None
        return await resp.json()

def get_solo_rank(leagues: list) -> dict:
    """Extract solo queue entry from league data."""
    if not leagues:
        return {}
    for entry in leagues:
        if entry.get("queueType") == "RANKED_SOLO_5x5":
            return entry
    return {}


def format_rank(rank_info:dict) -> str:
    """Format rank into a readable string."""
    if not rank_info:
        return "Unranked"
    tier = rank_info.get("tier", "Unranked").capitalize()
    division = rank_info.get("rank", "")
    lp = rank_info.get("leaguePoints", 0)
    return f"{tier} {division} — {lp} LP"

async def setup(bot):
    await bot.add_cog(ProfileCog(bot))
