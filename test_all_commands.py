import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from commands.login import LoginCog
from commands.profile import ProfileCog
from commands.recent import RecentCog

class TestCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.login_cog = LoginCog(self.bot)
        self.profile_cog = ProfileCog(self.bot)
        self.recent_cog = RecentCog(self.bot)

    async def test_login_success(self):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        with patch("commands.login.save_user") as mock_save, \
             patch("aiohttp.ClientSession.get") as mock_get:
            
            # Mock Riot Account API response
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json.return_value = {"puuid": "fake_puuid"}
            mock_get.return_value.__aenter__.return_value = mock_resp
            
            await self.login_cog.login.callback(self.login_cog, interaction, "TestUser#TAG")
            
            interaction.response.defer.assert_called_once()
            mock_save.assert_called_once_with("12345", "fake_puuid", "TestUser", "TAG")
            interaction.followup.send.assert_called_once()
            self.assertIn("Linked **TestUser#TAG**", interaction.followup.send.call_args[0][0])

    async def test_login_not_found(self):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_resp = AsyncMock()
            mock_resp.status = 404
            mock_get.return_value.__aenter__.return_value = mock_resp
            
            await self.login_cog.login.callback(self.login_cog, interaction, "NonExistent#TAG")
            
            interaction.followup.send.assert_called_once()
            self.assertIn("Summoner not found", interaction.followup.send.call_args[0][0])

    async def test_profile_not_linked(self):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        with patch("commands.profile.get_user", return_value=None):
            await self.profile_cog.profile.callback(self.profile_cog, interaction)
            
            interaction.followup.send.assert_called_once()
            self.assertIn("haven't linked your Riot account", interaction.followup.send.call_args[0][0])

    async def test_profile_success(self):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        # (discord_id, puuid, game_name, tag_line)
        mock_user = ("12345", "fake_puuid", "TestUser", "TAG")
        
        with patch("commands.profile.get_user", return_value=mock_user), \
             patch("commands.profile.fetch") as mock_fetch:
            
            # Mock Summoner Data
            mock_fetch.side_effect = [
                {"id": "summoner_id", "summonerLevel": 100}, # Summoner info
                [{"queueType": "RANKED_SOLO_5x5", "tier": "GOLD", "rank": "I", "leaguePoints": 50, "wins": 10, "losses": 5}] # League info
            ]
            
            await self.profile_cog.profile.callback(self.profile_cog, interaction)
            
            interaction.followup.send.assert_called_once()
            embed = interaction.followup.send.call_args[1]["embed"]
            self.assertEqual(embed.title, "📊 TestUser#TAG")
            self.assertIn("Gold I", embed.fields[1].value)

    async def test_recent_success(self):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.user.id = 12345
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()
        
        mock_user = ("12345", "fake_puuid", "TestUser", "TAG")
        
        with patch("commands.recent.get_user", return_value=mock_user), \
             patch("commands.recent.fetch") as mock_fetch, \
             patch("commands.recent.fetch_all") as mock_fetch_all:
            
            mock_fetch.return_value = ["match1"]
            mock_fetch_all.return_value = [{
                "metadata": {"matchId": "match1"},
                "info": {
                    "participants": [{"puuid": "fake_puuid", "win": True, "championName": "Lux", "kills": 10, "deaths": 2, "assists": 15, "totalMinionsKilled": 100, "neutralMinionsKilled": 10}],
                    "gameDuration": 1800,
                    "queueId": 420
                }
            }]
            
            await self.recent_cog.recent.callback(self.recent_cog, interaction, count=1)
            
            interaction.followup.send.assert_called_once()
            embeds = interaction.followup.send.call_args[1]["embeds"]
            self.assertEqual(len(embeds), 1)
            self.assertIn("Victory — Lux", embeds[0].title)

if __name__ == "__main__":
    unittest.main()
