import re
import logging
from core.stats_db import show_player_stats, show_session_stats, normalize_dice_type, DiceType

logger = logging.getLogger(__name__)

_VALID_DICE = {d.value for d in DiceType}
_VALID_DICE_LIST = ", ".join(sorted(_VALID_DICE))


def _parse_first_arg(arg):
    """Detect whether the first command arg is a dice type or a channel name.

    Returns (dice_type, channel_or_none). Raises ValueError for die-like but
    invalid values (e.g. 'd99').
    """
    if arg is None:
        return None, None
    normalized = arg.lower()
    if re.match(r'^\d+$', normalized):
        normalized = f"d{normalized}"
    if re.match(r'^d\d+$', normalized):
        if normalized in _VALID_DICE:
            return normalized, None
        raise ValueError(f"Unknown dice type '{arg}'. Valid types: {_VALID_DICE_LIST}")
    return None, arg


def commands_stats(bot, config_manager):
    @bot.command(
        name=config_manager.get_prefix("stats", "player"),
        help="Show stats per player in the channel"
    )
    async def command_show_stats_player(context, first=None, start_date=None, end_date=None, specific_player=None):
        try:
            dice_type, channel_arg = _parse_first_arg(first)
            channel = context.channel.name if dice_type else (channel_arg or context.channel.name)
            await show_player_stats(context,
                                    channel=channel,
                                    start_date=start_date,
                                    end_date=end_date,
                                    specific_player=specific_player,
                                    dice_type=dice_type)
        except ValueError as e:
            logger.warning(f"Invalid player stats parameters: {e}")
            await context.send(
                f"Invalid parameter. Use YYYY-MM-DD for dates or a valid dice type ({_VALID_DICE_LIST}). Examples:\n"
                "• `!my-stats` - Show your stats for current channel\n"
                "• `!my-stats d20` - Show only d20 stats\n"
                "• `!my-stats 2024-01-01 2024-12-31` - Stats for date range"
            )
        except Exception as e:
            logger.error(f"Error processing player stats: {e}", exc_info=True)
            await context.send("Sorry, I couldn't retrieve the player statistics. Make sure stats tracking is enabled.")

    @bot.command(
        name=config_manager.get_prefix("stats", "session"),
        help="Show stats per channel (session)"
    )
    async def command_show_stats_session(context, first=None, date=None, end_date=None):
        try:
            dice_type, channel_arg = _parse_first_arg(first)
            channel = context.channel.name if dice_type else (channel_arg or context.channel.name)
            await show_session_stats(context, channel, date, end_date, dice_type)
        except ValueError as e:
            logger.warning(f"Invalid session stats parameters: {e}")
            await context.send(
                f"Invalid parameter. Use YYYY-MM-DD for dates or a valid dice type ({_VALID_DICE_LIST}). Examples:\n"
                "• `!session-stats` - Show today's session stats\n"
                "• `!session-stats d20` - Session stats for d20 only\n"
                "• `!session-stats 2024-01-15` - Stats for specific date\n"
                "• `!session-stats d20 2024-01-01 2024-01-31` - d20 stats for date range"
            )
        except Exception as e:
            logger.error(f"Error processing session stats: {e}", exc_info=True)
            await context.send("Sorry, I couldn't retrieve the session statistics. Make sure stats tracking is enabled.")
