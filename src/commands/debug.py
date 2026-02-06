import os
import logging
from dotenv import load_dotenv
from core.helper import format_commands, format_plugin_commands


load_dotenv()
STATS_ENABLE = os.getenv("save_stats_db")

logger = logging.getLogger(__name__)


def commands_debug(bot, config_manager):
    @bot.event
    async def on_ready():
        logger.debug(
            f"I'm logged in as {bot.user.display_name} !\n Statistics enable: {STATS_ENABLE}.")

    @bot.command(name=config_manager.get_prefix("debug", "ping"))
    async def ping(context):
        latency_ms = bot.latency * 1000  # Convert from seconds to ms
        await context.send(f"Pong {context.author.nick} - {latency_ms:.2f} ms")

    @bot.command(name="sync", help="DO NOT CALL IF YOU DON'T KNOW WHAT YOU'RE DOING")
    async def sync(ctx):
        await bot.tree.sync()
        await ctx.send('Command tree synced.')
        logger.info("Command tree synced.")

    @bot.command(name=config_manager.get_prefix("debug", "help"), help="Show all available commands")
    async def send_help(context):
        try:
            help_text = "Here are the available commands:\n\n"
            help_text += format_commands(config_manager.config.items())
            await context.send(f"{help_text}")

            help_text = f"Plugins: \n"
            help_text += format_plugin_commands()
            await context.send(f"{help_text}")
        except Exception as e:
            logger.error(f"Error processing help message: {e}", exc_info=True)
            await context.send("Sorry, I couldn't fetch the help information.")
