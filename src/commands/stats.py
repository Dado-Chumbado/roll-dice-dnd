import logging
from core.stats_db import show_player_stats, show_session_stats

logger = logging.getLogger(__name__)


def commands_stats(bot, config_manager):
    @bot.command(
        name=config_manager.get_prefix("stats", "player"),
        help="Show stats per player in the channel"
    )
    async def command_show_stats_player(context, channel=None, start_date=None, end_date=None, specific_player=None ):
        try:
            await show_player_stats(context,
                                    channel=channel or context.channel.name,
                                    start_date=start_date,
                                    end_date=end_date,
                                    specific_player=specific_player)
        except ValueError as e:
            logger.warning(f"Invalid player stats parameters: {e}")
            await context.send(
                "Invalid date format! Use YYYY-MM-DD. Examples:\n"
                "• `!my-stats` - Show your stats for current channel\n"
                "• `!my-stats general 2024-01-01 2024-12-31` - Stats for date range"
            )
        except Exception as e:
            logger.error(f"Error processing player stats: {e}", exc_info=True)
            await context.send("Sorry, I couldn't retrieve the player statistics. Make sure stats tracking is enabled.")
    
    @bot.command(
        name=config_manager.get_prefix("stats", "session"),
        help="Show stats per channel (session)"
    )
    async def command_show_stats_session(context, channel='', date=None, end_date=None):
        try:
            print(f"Show session stats with date: {date} {end_date}")
            await show_session_stats(context, channel or context.channel.name, date, end_date)
        except ValueError as e:
            logger.warning(f"Invalid session stats parameters: {e}")
            await context.send(
                "Invalid date format! Use YYYY-MM-DD. Examples:\n"
                "• `!session-stats` - Show today's session stats\n"
                "• `!session-stats general 2024-01-15` - Stats for specific date\n"
                "• `!session-stats general 2024-01-01 2024-01-31` - Stats for date range"
            )
        except Exception as e:
            logger.error(f"Error processing session stats: {e}", exc_info=True)
            await context.send("Sorry, I couldn't retrieve the session statistics. Make sure stats tracking is enabled.")
