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
        async def new_char_roll(context, variant: str = None):
            """
            variant (optional):
              - "classic" or "4d6" => use 4d6 drop 1 lowest (old behaviour)
              - anything else / omitted => use 5d6 drop 2 lowest (new default)
            """
            if variant and variant.lower() in ("classic", "4d6"):
                dice_expr = "4d6+4d6+4d6+4d6+4d6+4d6"
                drop_count = 1
            else:
                dice_expr = "5d6+5d6+5d6+5d6+5d6+5d6"
                drop_count = 2

            rolls, dice_data, reroll = await process_input_dice(context, dice_expr)

            roll = rolls[0]
            # disable the N smallest dice for each stat; handle APIs that accept a count or require repeated calls
            for rolled in roll.rolled_sum_dice:
                try:
                    rolled.disable_smaller(drop_count)
                except TypeError:
                    for _ in range(drop_count):
                        rolled.disable_smaller()

            await context.send(
                await get_new_char_roll_text(context, roll))
