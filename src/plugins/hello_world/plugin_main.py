import os
from config import ConfigManager
from plugin_manager import Plugin
import logging


logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)  # Get the current script's directory


class PluginMain(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.config_manager = ConfigManager(os.path.join(current_folder, 'config.json'))
        self.commands_plugin(bot, self.config_manager)
        print(f"Plugin {self.__class__.__name__} initialized!")

    def commands_plugin(self, bot, cm):
        @bot.event
        async def on_ready():
            logging.debug(
                f"Plugin {self.__class__.__name__} loaded!")

        @bot.command(
            name=cm.get_prefix("hello_world", "default"),
            description=cm.get_description("hello_world", "default")
        )
        async def say_hello_world(context):
            await context.send(f"Hello World")
