import discord
from discord import app_commands
from discord.ext import commands
import os

from database.db import get_user
from services.riot_api import get_summoner, get_rank

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
                "❌ You haven't linked your Riot account yet. Use `/signin` first."
            )
            return

        _, puuid, game_name, tag_line = user
        
        # 1. Get summoner data (level) via PUUID
        summoner = await get_summoner(puuid)
        print(f"DEBUG: summoner response for {puuid}: {summoner}")
        
        if not summoner:
            await interaction.followup.send("❌ Could not fetch summoner data (Summoner not found).")
            return
        
        if isinstance(summoner, dict) and "error" in summoner:
            if summoner["error"] == 401:
                await interaction.followup.send("❌ Riot API error (401): Unauthorized. API Key might be expired.")
            elif summoner["error"] == 403:
                await interaction.followup.send("❌ Riot API error (403): Forbidden. Your API Key is likely EXPIRED. Please regenerate it at developer.riotgames.com.")
            else:
                await interaction.followup.send(f"❌ Riot API error ({summoner['error']}).")
            return

        # Ensure 'id' exists before accessing it
        # Fallback to puuid if 'id' is missing (some newer API behavior)
        summoner_id = summoner.get("id") or summoner.get("puuid")
        
        if not summoner_id:
             await interaction.followup.send(f"❌ Could not find a valid ID in Riot API response. Keys: {list(summoner.keys())}")
             return

        level = summoner.get("summonerLevel", "N/A")

        # 2. Get rank & LP (League-v4)
        leagues = await get_rank(summoner_id)
        
        if leagues is None:
            leagues = []
        elif isinstance(leagues, dict) and "error" in leagues:
            await interaction.followup.send(f"❌ Riot API error ({leagues['error']}).")
            return

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
def get_solo_rank(leagues) -> dict:
    """Extract solo queue entry from league data."""
    if not isinstance(leagues, list) or not leagues:
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
