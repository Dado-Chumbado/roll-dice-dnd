import os
import logging
from dotenv import load_dotenv
from core.helper import format_commands


load_dotenv()
STATS_ENABLE = os.getenv("save_stats_db")

logger = logging.getLogger(__name__)


def commands_debug(bot, config_manager):
    @bot.event
    async def on_ready():
        logging.debug(
            f"I'm logged in as {bot.user.display_name} !\n Statistics enable: {STATS_ENABLE}.")

    @bot.command(name=config_manager.get_prefix("debug", "ping"))
    async def ping(context):
        latency_ms = bot.latency * 1000  # Convert from seconds to ms
        await context.send(f"Pong {context.author.nick} - {latency_ms:.2f} ms")

    @bot.command(name="sync")
    async def sync(ctx):
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
        logging.info("Command tree synced.")

    @bot.command(name=config_manager.get_prefix("debug", "help"), help="Show all available commands")
    async def send_help(context):
        try:
            help_text = format_commands(config_manager)
            await context.send(f"{help_text}")
        except Exception as e:
            logging.error(f"Error processing help message: {e}")
            await context.send(f"An error occurred while fetching the commands: {e}")
