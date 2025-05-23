import os
from config import ConfigManager
from core.dice_engine import process_input_dice
from plugin_manager import Plugin
import logging

from plugins.new_char.utils import get_new_char_roll_text

logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)  # Get the current script's directory


class PluginNewChar(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.cm = ConfigManager(os.path.join(current_folder, 'plugin_config.json'))
        self.commands_plugin(bot)
        logging.info(f"{self.__class__.__name__} initialized!")

    def commands_plugin(self, bot):
        @bot.event
        async def on_ready():
            logging.debug(
                f"{self.__class__.__name__} loaded!")

        @bot.command(
            name=self.cm.get_prefix("new_char", "default"),
            help=self.cm.get_description("new_char", "default")
        )
        async def new_char_roll(context):
            rolls, dice_data, reroll = await process_input_dice(context,
                                                                "4d6+4d6+4d6+4d6+4d6+4d6")

            roll = rolls[0]
            # Disable smaller roll results
            for rolled in roll.rolled_sum_dice:
                rolled.disable_smaller()
            await context.send(
                await get_new_char_roll_text(context, roll))
