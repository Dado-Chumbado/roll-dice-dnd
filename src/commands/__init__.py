from .debug import commands_debug
from .roll_dice import commands_dice
from .initiative import commands_initiative
from .stats import commands_stats
from .dice_storage import commands_storage

def commands_setup(bot):
    commands_debug(bot)
    commands_dice(bot)
    commands_initiative(bot)
    commands_stats(bot)
    commands_storage(bot)
