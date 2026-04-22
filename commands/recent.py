import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os 
from database.db import get_user

RIOT_API_KEY = os.getenv("LEAGUEAPI")
REGION = "na1"
CLUSTER = "americas" 

CLUSTER_MAP = {
    "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
    "euw1": "europe",  "eun1": "europe",  "tr1": "europe",   "ru": "europe",
    "kr": "asia",      "jp1": "asia",
}
class RecentCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name = "recent", description="Show your last N matches")
    @app_commands.describe(count="Number of matches to show (1–10, default 5)")
    async def recent(self , interaction: discord.Interaction, count: int = 5):
        await interaction.response.defer(ephemeral=False)

        count = max(1, min(count, 10))  # clamp between 1 and 10
        discord_id = str(interaction.user.id)
        user = get_user(discord_id)
            
        #check if user
        if not user:
            await interaction.followup.send(
                "❌ You haven't linked your account yet. Use `/signin` first."
            )
            return

        #get user
        _, puuid, game_name, tag_line = user
        cluster = CLUSTER_MAP.get(REGION, "americas")
        headers = {"X-Riot-Token": RIOT_API_KEY}
        
        #get user data
        async with aiohttp.ClientSession() as session:
            # 1. Fetch match ID list
            match_ids = await fetch(
                session,
                f"https://{cluster}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}",
                headers
            )
            if not match_ids:
                await interaction.followup.send("❌ Could not fetch match history.")
                return

            # 2. Fetch each match in parallel
            match_data = await fetch_all(session, [
                f"https://{cluster}.api.riotgames.com/lol/match/v5/matches/{mid}"
                for mid in match_ids
            ], headers)
        embeds = []
        for match in match_data:
            if match:
                embed = build_match_embed(match , puuid, game_name,tag_line)
                if embed:
                    embeds.append(embed)
        if not embeds:
            await interaction.followup.send("❌ No recent matches found.")
            return

        # Discord allows max 10 embeds per message
        await interaction.followup.send(embeds=embeds[:10])








# ── Helpers ────────────────────────────────────────────────────────────────────

async def fetch(session: aiohttp.ClientSession, url: str, headers: dict):
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return None
        return await resp.json()


async def fetch_all(session: aiohttp.ClientSession, urls: list, headers: dict):
    """Fetch multiple URLs concurrently."""
    import asyncio
    return await asyncio.gather(*[fetch(session, url, headers) for url in urls])


def get_player(match: dict, puuid: str) -> dict:
    """Find this player's participant data within the match."""
    participants = match["info"]["participants"]
    return next((p for p in participants if p["puuid"] == puuid), None)


def format_kda(kills, deaths, assists) -> str:
    ratio = (kills + assists) / max(deaths, 1)
    return f"{kills}/{deaths}/{assists} ({ratio:.2f} KDA)"


def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"


def queue_name(queue_id: int) -> str:
    queues = {
        420: "Ranked Solo",
        440: "Ranked Flex",
        450: "ARAM",
        400: "Normal Draft",
        430: "Normal Blind",
    }
    return queues.get(queue_id, "Other")


def build_match_embed(match: dict, puuid: str, game_name: str, tag_line: str):
    player = get_player(match, puuid)
    if not player:
        return None

    won         = player["win"]
    champion    = player["championName"]
    kills       = player["kills"]
    deaths      = player["deaths"]
    assists     = player["assists"]
    cs          = player["totalMinionsKilled"] + player["neutralMinionsKilled"]
    duration    = match["info"]["gameDuration"]
    queue_id    = match["info"]["queueId"]
    cs_per_min  = round(cs / max(duration / 60, 1), 1)

    color  = 0x2ecc71 if won else 0xe74c3c   # green = win, red = loss
    result = "✅ Victory" if won else "❌ Defeat"

    embed = discord.Embed(
        title=f"{result} — {champion}",
        description=f"**{queue_name(queue_id)}** · {format_duration(duration)}",
        color=color
    )
    embed.add_field(name="⚔️ KDA",    value=format_kda(kills, deaths, assists), inline=True)
    embed.add_field(name="🌾 CS",     value=f"{cs} ({cs_per_min}/min)",          inline=True)
    embed.add_field(name="👤 Player", value=f"{game_name}#{tag_line}",           inline=True)
    embed.set_thumbnail(
        url=f"https://ddragon.leagueoflegends.com/cdn/14.8.1/img/champion/{champion}.png"
    )

    return embed

#---------------------------------------------------------------------------

#how to start the bot
async def setup(bot):
    await bot.add_cog(RecentCog(bot))
