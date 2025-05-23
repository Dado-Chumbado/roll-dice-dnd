from commands.debug import commands_debug
from commands.roll_dice import commands_dice
from commands.initiative import commands_initiative
from commands.stats import commands_stats
from plugin_manager import load_plugins
import logging
logger = logging.getLogger(__name__)

def commands_setup(bot, config_manager):
    commands_debug(bot, config_manager)
    commands_dice(bot, config_manager)
    commands_initiative(bot, config_manager)
    commands_stats(bot, config_manager)

    # Load the plugins dynamically from the plugin folder
    plugins = load_plugins()
    logger.info(f"Loading {len(plugins)} plugins")

    # Instantiate and register each plugin, passing the bot instance
    for plugin in plugins:
        plugin(bot)
        # TODO: Fix this, the "name" is incorrect
        logger.info(f"Plugin: {plugin.__class__.__name__} ready!")
