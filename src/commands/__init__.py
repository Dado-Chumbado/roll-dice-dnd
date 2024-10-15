from commands.debug import commands_debug
from commands.roll_dice import commands_dice
from commands.initiative import commands_initiative
from commands.stats import commands_stats
from plugin_manager import load_plugins

def commands_setup(bot, config_manager):
    commands_debug(bot, config_manager)
    commands_dice(bot, config_manager)
    commands_initiative(bot, config_manager)
    commands_stats(bot, config_manager)

    # Use loaded plugins
    plugins = load_plugins()
    print(plugins)
    for plugin in plugins:
        plugin(bot)