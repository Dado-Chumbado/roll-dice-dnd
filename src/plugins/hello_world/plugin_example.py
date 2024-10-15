import os
from config import ConfigManager
from plugin_manager import Plugin
import logging


logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)  # Get the current script's directory


class PluginExample(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.cm = ConfigManager(os.path.join(current_folder, 'config.json'))
        self.commands_plugin(bot)
        logging.info(f"{self.__class__.__name__} initialized!")

    def commands_plugin(self, bot):
        @bot.command(
            name=self.cm.get_prefix("hello_world", "default"),
            description=self.cm.get_description("hello_world", "default")
        )
        async def say_hello_world(context):
            await context.send(f"Hello World")
