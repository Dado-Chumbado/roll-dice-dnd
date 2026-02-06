import os
import logging
from dotenv import load_dotenv
from core.helper import format_commands, format_plugin_commands
from core.dm_manager import dm_manager


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

    @bot.command(name=config_manager.get_prefix("debug", "set_dm"), help="Set the DM for this channel")
    async def set_dm(context, member=None):
        try:
            # If a member is mentioned, use them
            if context.message.mentions:
                dm_user = context.message.mentions[0]
            # Otherwise, use the command author
            else:
                dm_user = context.author

            # Set the DM for this channel
            dm_manager.set_dm(
                context.channel.name,
                dm_user.id,
                dm_user.display_name
            )

            await context.send(
                f"✅ **DM set for this channel:** {dm_user.mention}\n"
                f"All `!dm` rolls will now be sent to {dm_user.display_name}'s DMs."
            )

        except Exception as e:
            logger.error(f"Error setting DM: {e}", exc_info=True)
            await context.send("Sorry, I couldn't set the DM. Please try again.")

    @bot.command(name=config_manager.get_prefix("debug", "show_dm"), help="Show the current DM for this channel")
    async def show_dm(context):
        try:
            dm_info = dm_manager.get_dm(context.channel.name)

            if dm_info:
                # Try to get the user object to mention them
                try:
                    dm_user = await bot.fetch_user(dm_info['user_id'])
                    await context.send(
                        f"📜 **Current DM for this channel:** {dm_user.mention} ({dm_info['username']})"
                    )
                except:
                    await context.send(
                        f"📜 **Current DM for this channel:** {dm_info['username']}"
                    )
            else:
                await context.send(
                    "❌ No DM set for this channel.\n"
                    "Use `!set-dm` to set yourself as DM, or `!set-dm @username` to set someone else."
                )

        except Exception as e:
            logger.error(f"Error showing DM: {e}", exc_info=True)
            await context.send("Sorry, I couldn't retrieve the DM information.")
