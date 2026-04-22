import discord
from dataclasses import dataclass

# ── Data class ─────────────────────────────────────────────────────────────────


@dataclass
class MatchSummary:
    match_id: str
    champion: str
    won: bool
    kills: int
    deaths: int
    assists: int
    cs: int
    vision: int
    damage: int
    gold: int
    duration: int  # seconds
    queue_id: int
    items: list[int]
    spell1_id: int
    spell2_id: int
    game_name: str
    tag_line: str
    patch: str


# ── Parser ─────────────────────────────────────────────────────────────────────


def parse_match(
    match: dict, puuid: str, game_name: str, tag_line: str, patch: str
) -> MatchSummary | None:
    """Extract a clean MatchSummary from raw Riot API match data."""
    participants = match["info"]["participants"]
    player = next((p for p in participants if p["puuid"] == puuid), None)

    if not player:
        return None

    return MatchSummary(
        match_id=match["metadata"]["matchId"],
        champion=player["championName"],
        won=player["win"],
        kills=player["kills"],
        deaths=player["deaths"],
        assists=player["assists"],
        cs=player["totalMinionsKilled"] + player["neutralMinionsKilled"],
        vision=player["visionScore"],
        damage=player["totalDamageDealtToChampions"],
        gold=player["goldEarned"],
        duration=match["info"]["gameDuration"],
        queue_id=match["info"]["queueId"],
        items=[player[f"item{i}"] for i in range(7) if player.get(f"item{i}", 0) != 0],
        spell1_id=player["summoner1Id"],
        spell2_id=player["summoner2Id"],
        game_name=game_name,
        tag_line=tag_line,
        patch=patch,
    )


# ── Formatters ─────────────────────────────────────────────────────────────────


def fmt_kda(kills: int, deaths: int, assists: int) -> str:
    ratio = (kills + assists) / max(deaths, 1)
    return f"{kills}/{deaths}/{assists} ({ratio:.2f} KDA)"


def fmt_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"


def fmt_cs(cs: int, duration: int) -> str:
    per_min = round(cs / max(duration / 60, 1), 1)
    return f"{cs} ({per_min}/min)"


def fmt_damage(damage: int) -> str:
    return f"{damage:,}"


def fmt_gold(gold: int) -> str:
    return f"{gold:,} g"


def fmt_rank_entry(entry: dict | None) -> str:
    if not entry:
        return "Unranked"
    tier = entry["tier"].capitalize()
    division = entry["rank"]
    lp = entry["leaguePoints"]
    wins = entry["wins"]
    losses = entry["losses"]
    total = wins + losses
    wr = f"{round(wins / total * 100)}%" if total > 0 else "N/A"
    return f"{tier} {division} — {lp} LP ({wr} WR)"


QUEUE_NAMES = {
    420: "Ranked Solo/Duo",
    440: "Ranked Flex",
    450: "ARAM",
    400: "Normal Draft",
    430: "Normal Blind",
    900: "URF",
    1020: "One for All",
    1300: "Nexus Blitz",
}

SUMMONER_SPELL_NAMES = {
    1: "Cleanse",
    3: "Exhaust",
    4: "Flash",
    6: "Ghost",
    7: "Heal",
    11: "Smite",
    12: "Teleport",
    13: "Clarity",
    14: "Ignite",
    21: "Barrier",
    32: "Mark",
}


def fmt_queue(queue_id: int) -> str:
    return QUEUE_NAMES.get(queue_id, "Other")


def fmt_spells(spell1_id: int, spell2_id: int) -> str:
    s1 = SUMMONER_SPELL_NAMES.get(spell1_id, f"#{spell1_id}")
    s2 = SUMMONER_SPELL_NAMES.get(spell2_id, f"#{spell2_id}")
    return f"{s1} / {s2}"


# ── Embed builders ─────────────────────────────────────────────────────────────


def build_match_embed(s: MatchSummary) -> discord.Embed:
    """Full match embed with all stats."""
    result = "✅ Victory" if s.won else "❌ Defeat"
    color = 0x2ECC71 if s.won else 0xE74C3C

    embed = discord.Embed(
        title=f"{result} — {s.champion}",
        description=f"**{fmt_queue(s.queue_id)}** · {fmt_duration(s.duration)}",
        color=color,
    )

    embed.add_field(
        name="⚔️ KDA", value=fmt_kda(s.kills, s.deaths, s.assists), inline=True
    )
    embed.add_field(name="🌾 CS", value=fmt_cs(s.cs, s.duration), inline=True)
    embed.add_field(name="👁️ Vision", value=str(s.vision), inline=True)
    embed.add_field(name="💥 Damage", value=fmt_damage(s.damage), inline=True)
    embed.add_field(name="💰 Gold", value=fmt_gold(s.gold), inline=True)
    embed.add_field(
        name="🔮 Spells", value=fmt_spells(s.spell1_id, s.spell2_id), inline=True
    )
    embed.add_field(name="👤 Player", value=f"{s.game_name}#{s.tag_line}", inline=False)

    embed.set_thumbnail(
        url=f"https://ddragon.leagueoflegends.com/cdn/{s.patch}/img/champion/{s.champion}.png"
    )
    embed.set_footer(text=f"Match ID: {s.match_id}")

    return embed


def build_compact_embed(s: MatchSummary) -> discord.Embed:
    """Minimal one-liner embed, good for showing many matches at once."""
    result = "✅" if s.won else "❌"
    color = 0x2ECC71 if s.won else 0xE74C3C
    kda = fmt_kda(s.kills, s.deaths, s.assists)
    cs = fmt_cs(s.cs, s.duration)

    embed = discord.Embed(
        description=(
            f"{result} **{s.champion}** · {fmt_queue(s.queue_id)} · {fmt_duration(s.duration)}\n"
            f"⚔️ {kda} · 🌾 {cs} · 💥 {fmt_damage(s.damage)}"
        ),
        color=color,
    )
    embed.set_thumbnail(
        url=f"https://ddragon.leagueoflegends.com/cdn/{s.patch}/img/champion/{s.champion}.png"
    )
    return embed


def build_match_list_embed(
    summaries: list[MatchSummary], game_name: str, tag_line: str
) -> discord.Embed:
    """Single embed summarizing multiple matches at once."""
    total = len(summaries)
    wins = sum(1 for s in summaries if s.won)
    losses = total - wins
    wr = f"{round(wins / total * 100)}%" if total > 0 else "N/A"

    avg_kda = sum((s.kills + s.assists) / max(s.deaths, 1) for s in summaries) / max(
        total, 1
    )

    embed = discord.Embed(
        title=f"📋 Last {total} matches — {game_name}#{tag_line}",
        description=f"**{wins}W / {losses}L** · {wr} WR · {avg_kda:.2f} avg KDA",
        color=0x1A78C2,
    )

    for s in summaries:
        result = "✅" if s.won else "❌"
        embed.add_field(
            name=f"{result} {s.champion} — {fmt_queue(s.queue_id)}",
            value=(
                f"⚔️ {fmt_kda(s.kills, s.deaths, s.assists)} · "
                f"🌾 {fmt_cs(s.cs, s.duration)} · "
                f"⏱️ {fmt_duration(s.duration)}"
            ),
            inline=False,
        )
    return embed
