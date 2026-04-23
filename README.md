# LoL Discord Bot 🎮

A Discord bot that integrates with the Riot Games API to provide League of Legends player profiles, match history, and account linking.

## Features

-   **Account Linking:** Link your Riot account to your Discord ID for easy access.
-   **Player Profile:** View comprehensive player statistics, ranks, and basic info.
-   **Match History:** Check your recent matches with detailed performance stats.
-   **Slash Commands:** Fully supports Discord slash commands for a modern experience.

## Commands

-   `/login [game_name] [tag_line]` - Link your Riot Games account to your Discord profile.
-   `/profile [game_name] [tag_line]` - Display a player's League of Legends profile (defaults to your linked account).
-   `/recent [game_name] [tag_line]` - Show the most recent match for a player.
-   `/ping` - Check the bot's latency.

## Setup & Installation

### Prerequisites

-   Python 3.8+
-   A Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
-   A Riot Games API Key (from [Riot Developer Portal](https://developer.riotgames.com/))

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Rainyy21/lol_discordbot.git
    cd lol_discordbot
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```env
    DISCORDTOKEN=your_discord_bot_token
    RIOT_API_KEY=your_riot_api_key
    SERVER_ID=your_discord_server_id (optional, for faster command syncing)
    ```

4.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Project Structure

-   `bot.py`: Main entry point for the Discord bot.
-   `commands/`: Contains slash command definitions (login, profile, recent).
-   `services/`: Business logic for Riot API interaction and data formatting.
-   `database/`: SQLite database management for storing user links and match data.

## License

This project is for educational purposes. League of Legends and Riot Games are trademarks or registered trademarks of Riot Games, Inc.
