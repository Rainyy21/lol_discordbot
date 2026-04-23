import discord
from discord import app_commands
from discord.ext import commands
import os
from database.db import save_user
from services.riot_api import get_account

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

        # Use the service instead of direct API call
        data = await get_account(game_name, tag_line)

        if data is None:
            await interaction.followup.send("❌ Summoner not found. Check your Riot ID.", ephemeral=True)
            return

        if isinstance(data, dict) and "error" in data:
            if data["error"] == 401:
                await interaction.followup.send(
                    "❌ Riot API error (401): Unauthorized. "
                    "This usually means the bot's API key has expired. "
                    "Please notify the bot owner to refresh it at developer.riotgames.com.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Riot API error ({data['error']}). Try again later.",
                    ephemeral=True
                )
            return

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


async def setup(bot):
    await bot.add_cog(LoginCog(bot))

