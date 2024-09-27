from .debug import commands_debug
from .roll_dice import commands_dice
from .initiative import commands_initiative
from .stats import commands_stats

def commands_setup(bot):
    commands_debug(bot)
    commands_dice(bot)
    commands_initiative(bot)
    commands_stats(bot)
