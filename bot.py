import discord
from discord.ext import commands, tasks
import asyncio
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),  # also print to console
    ],
)
log = logging.getLogger("bot")


# ── Bot setup ──────────────────────────────────────────────────────────────────

EXTENSIONS = [
    "commands.login",
    "commands.profile",
    "commands.recent",
]


class LoLBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,  # disable default help
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def setup_hook(self):
        """Called once before the bot connects — load extensions here."""
        for ext in EXTENSIONS:
            try:
                await self.load_extension(ext)
                log.info(f"✅ Loaded extension: {ext}")
            except Exception as e:
                log.error(f"❌ Failed to load {ext}: {e}")

        # If SERVER_ID is provided, sync specifically to that guild for instant updates
        guild_id = os.getenv("SERVER_ID")
        if guild_id:
            try:
                guild = discord.Object(id=int(guild_id))
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                log.info(f"🔄 Slash commands synced to guild {guild_id}")
            except Exception as e:
                log.error(f"❌ Failed to sync to guild {guild_id}: {e}")
        
        await self.tree.sync()
        log.info("🔄 Global slash commands synced")

    async def on_ready(self):
        log.info(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        log.info(f"   Guilds : {len(self.guilds)}")
        log.info(f"   Ping   : {round(self.latency * 1000)}ms")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="League of Legends 🎮"
            )
        )

        self.status_task.start()

    async def on_disconnect(self):
        log.warning("⚠️  Bot disconnected from Discord")

    async def on_resumed(self):
        log.info("🔄 Bot reconnected")

    # ── Error handling ─────────────────────────────────────────────────────────

    async def on_command_error(self, ctx, error):
        log.error(f"Command error in {ctx.command}: {error}")

    async def on_application_command_error(
        self, interaction: discord.Interaction, error
    ):
        log.error(f"Slash command error: {error}")
        msg = "❌ Something went wrong. Please try again later."

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    async def on_guild_join(self, guild: discord.Guild):
        log.info(f"➕ Joined guild: {guild.name} (ID: {guild.id})")

    async def on_guild_remove(self, guild: discord.Guild):
        log.info(f"➖ Left guild: {guild.name} (ID: {guild.id})")

    # ── Background task ────────────────────────────────────────────────────────

    @tasks.loop(minutes=30)
    async def status_task(self):
        """Rotate bot status every 30 minutes."""
        statuses = [
            discord.Activity(
                type=discord.ActivityType.watching, name="League of Legends 🎮"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="/login | /profile | /recent"
            ),
            discord.Activity(
                type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"
            ),
        ]
        index = (self.status_task.current_loop) % len(statuses)
        await self.change_presence(activity=statuses[index])

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()


# ── Dev commands (owner only) ──────────────────────────────────────────────────

bot = LoLBot()


@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx, guild: str = None):
    """Force re-sync slash commands. Use 'guild' to sync to current guild."""
    if guild == "guild":
        bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Slash commands synced to **{ctx.guild.name}**.")
        log.info(f"🔄 Manual sync triggered for guild {ctx.guild.id}")
    else:
        await bot.tree.sync()
        await ctx.send("✅ Global slash commands synced (may take an hour).")
        log.info("🔄 Manual global sync triggered")


@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx, extension: str):
    """Reload a specific extension (owner only). Usage: !reload commands.login"""
    try:
        await bot.reload_extension(extension)
        await ctx.send(f"✅ Reloaded `{extension}`")
        log.info(f"🔄 Reloaded extension: {extension}")
    except Exception as e:
        await ctx.send(f"❌ Failed: {e}")
        log.error(f"Reload failed for {extension}: {e}")


@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    """Check bot latency."""
    await interaction.response.send_message(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")


@bot.command(name="status")
@commands.is_owner()
async def status(ctx):
    """Show bot status info (owner only)."""
    uptime = datetime.now(timezone.utc) - bot.start_time if hasattr(bot, "start_time") else "N/A"
    embed = discord.Embed(title="🤖 Bot Status", color=0x1A78C2)
    embed.add_field(name="📡 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="🏠 Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="🔌 Shards", value=str(bot.shard_count or 1), inline=True)
    await ctx.send(embed=embed)


# ── Entry point ────────────────────────────────────────────────────────────────


async def main():
    token = os.getenv("DISCORDTOKEN")
    if not token:
        log.critical("❌ DISCORDTOKEN not found in .env — exiting")
        return

    async with bot:
        bot.start_time = datetime.now(timezone.utc)
        await bot.start(token)


asyncio.run(main())
