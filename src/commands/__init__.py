from .debug import commands_debug
from .roll_dice import commands_dice
from .initiative import commands_initiative
from .stats import commands_stats

def commands_setup(bot, config_manager):
    commands_debug(bot, config_manager)
    commands_dice(bot, config_manager)
    commands_initiative(bot, config_manager)
    commands_stats(bot, config_manager)
