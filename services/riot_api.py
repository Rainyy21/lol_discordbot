import aiohttp
import asyncio
import os
import json
from dotenv import load_dotenv
from db import save_match, get_match as get_cached_match

RIOT_API_KEY = os.getenv("LEAGUEAPI")
REGION = os.getenv("REGION", "na1")

CLUSTER_MAP = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp1": "asia",
}
CLUSTER = CLUSTER_MAP.get(REGION, "americas")


async def riot_get(url: str, retries: int = 3) -> dict | list | None:
    headers = {"X-Riot-Token": RIOT_API_KEY}
    async with aiohttp.ClientSession() as session:
        for attempt in range(retries):
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 492:
                    wait = int(resp.headers.get("Retry-After", 5))
                    print(f"⚠️  Rate limited. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                elif resp.status == 404:
                    return None
                else:
                    print(f"❌ Error {resp.status} (attempt {attempt + 1}): {url}")
                    await asyncio.sleep(1)

    return None


# ── Endpoints ──────────────────────────────────────────────────────────────────


async def get_account(game_name: str, tag_line: str) -> dict | None:
    return await riot_get(
        f"https://{CLUSTER}.api.riotgames.com"
        f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    )


async def get_summoner(puuid: str) -> dict | None:
    return await riot_get(
        f"https://{REGION}.api.riotgames.com"
        f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    )


async def get_rank(summoner_id: str) -> dict | None:
    return await riot_get(
        f"https://{REGION}.api.riotgames.com"
        f"/lol/league/v4/entries/by-summoner/{summoner_id}"
    )


async def get_match_ids(puuid: str, count: int = 5) -> dict | None:
    return await riot_get(
        f"https://{CLUSTER}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    )


async def get_match(match_id: str) -> dict | None:
    # check cache first
    cached = get_cached_match(match_id)
    if cached:
        return json.loads(cached)
    data = await riot_get(
        f"https://{CLUSTER}.api.riotgames.com" f"/lol/match/v5/matches/{match_id}"
    )
    if data:
        save_match(match_id, json.dumps(data))
    return data


async def get_latest_patch() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://ddragon.leagueoflegends.com/api/versions.json"
        ) as resp:
            versions = await resp.json()
            return versions[0] if versions else "14.8.1"
