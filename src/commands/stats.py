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
        except Exception as e:
            logging.error(f"Error processing stats: {e}")
            await context.send(f"Exception {e}")
    
    @bot.command(
        name=config_manager.get_prefix("stats", "session"),
        help="Show stats per channel (session)"
    )
    async def command_show_stats_session(context, channel='', date=None, end_date=None):
        try:
            print(f"Show session stats with date: {date} {end_date}")
            await show_session_stats(context, channel or context.channel.name, date, end_date)
        except Exception as e:
            logging.error(f"Error processing session stats: {e}")
            await context.send(f"Exception {e}")
