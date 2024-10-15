import os
from config import ConfigManager
from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text
from plugin_manager import Plugin
import logging

import json
import random


logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)  # Get the current script's directory


def load_json(filename='magic_tables.json'):
    with open(os.path.join(current_folder, filename), 'r') as f:
        data = json.load(f)
        return data

def find_effect(roll, data):
    for effect in data:
        if effect['range'][0] <= roll <= effect['range'][-1]:
            return effect['description']
    return "No effect found for this roll"  # In case no matching range is found

class PluginMagic(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.cm = ConfigManager(os.path.join(current_folder, 'config.json'))
        self.commands_plugin(bot)
        self.magic_list = load_json()
        logging.info(f"{self.__class__.__name__} initialized!")

    def commands_plugin(self, bot):
        @bot.command(
            name=self.cm.get_prefix("magic", "luck"),
            description=self.cm.get_description("magic", "luck")
        )
        async def say_hello_world(ctx):

            # Assume the JSON is loaded into a variable called 'data'
            effects = self.magic_list["magic_luck"]

            rolls, dice_data, reroll = await process_input_dice(ctx, "1d100")
            roll = rolls[0]
            logging.debug(f"Magic Roll: {roll}")
            await ctx.send(
                await get_roll_text(ctx, roll, dice_data, reroll))

            descriptions = find_effect(roll.total_dice_result, effects)
            await ctx.send(f"\n **{descriptions}**")
