import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from database.db import save_user

RIOT_API_KEY = os.getenv("LEAGUEAPI")

class LoginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _handle_login(self, interaction: discord.Interaction, summoner: str):
        await interaction.response.defer(ephemeral=True)
        
        if "#" not in summoner:
            await interaction.followup.send("❌ Use the format `Name#TAG`", ephemeral=True)
            return

        try:
            game_name, tag_line = summoner.split("#", 1)
        except ValueError:
            await interaction.followup.send("❌ Invalid format. Use `Name#TAG`", ephemeral=True)
            return

        discord_id = str(interaction.user.id)

        url = (
            f"https://americas.api.riotgames.com/riot/account/v1/accounts"
            f"/by-riot-id/{game_name}/{tag_line}"
        )
        headers = {"X-Riot-Token": RIOT_API_KEY}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 404:
                    await interaction.followup.send("❌ Summoner not found. Check your Riot ID.", ephemeral=True)
                    return
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Riot API error ({resp.status}). Try again later.", ephemeral=True)
                    return

                data = await resp.json()
                puuid = data["puuid"]

        save_user(discord_id, puuid, game_name, tag_line)

        await interaction.followup.send(
            f"✅ Linked **{game_name}#{tag_line}** to your Discord account!",
            ephemeral=True
        )

    @app_commands.command(name="login", description="Link your Riot account")
    @app_commands.describe(summoner="Your Riot ID (e.g. Name#TAG)")
    async def login(self, interaction: discord.Interaction, summoner: str):
        await self._handle_login(interaction, summoner)

    @app_commands.command(name="signin", description="Link your Riot account")
    @app_commands.describe(summoner="Your Riot ID (e.g. Name#TAG)")
    async def signin(self, interaction: discord.Interaction, summoner: str):
        await self._handle_login(interaction, summoner)


async def setup(bot):
    await bot.add_cog(LoginCog(bot))

