from config import stats_commands
from core.stats_db import show_general_info, show_session_stats


def commands_stats(bot):
    @bot.command(
        name=stats_commands.get("player"),
        description="Show stats per player in the channel"
    )
    async def command_show_stats_player(context):
        try:
            await show_general_info(context)
        except Exception as e:
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=stats_commands.get("session"),
        description="Show stats per channel (session)"
    )
    async def command_show_stats_session(context, date=None, end_date=None):
        try:
            print(f"date: {date}")
            await show_session_stats(context, context.channel.name, date, end_date)
        except Exception as e:
            await context.send(f"Exception {e}")