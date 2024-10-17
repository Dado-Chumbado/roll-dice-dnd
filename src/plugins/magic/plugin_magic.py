import os
from config import ConfigManager
from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text
from plugin_manager import Plugin
from enum import Enum
import logging
import json
import random


class EffectType(Enum):
    NORMAL = "magic_surge"
    FEY = "magic_surge_fey"


logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)  # Get the current script's directory
magic_surge_type = EffectType.FEY.value


def load_json(filename) -> json:
    with open(os.path.join(current_folder, filename), 'r') as f:
        data = json.load(f)
        return data


def find_effect(roll, data):
    for effect in data:
        if effect['range'][0] <= roll <= effect['range'][-1]:
            return effect
    return None


def get_magic_surge_effect(roll, data):
    # get the correct list of effect based on magic_surge_type
    for effect in data[magic_surge_type]:
        if effect['range'][0] <= roll <= effect['range'][-1]:
            return effect
    return None

def get_failed_magic_surge_effect(roll, data):
    # Find the exaclty same effect
    for effect in data:
        if effect['range'][0] == roll:
            return effect
    return None


class PluginMagic(Plugin):
    def __init__(self, bot):
        super().__init__(bot)

        self.cm = ConfigManager(os.path.join(current_folder, 'plugin_config.json'))
        self.commands_plugin(bot)
        self.magic_list = load_json('magic_tables.json')
        self.magic_surge_list = load_json('magic_surge.json')
        self.magic_fail_list = load_json('magic_fail.json')
        logging.info(f"{self.__class__.__name__} initialized!")

    def commands_plugin(self, bot):
        @bot.command(
            name=self.cm.get_prefix("magic", "luck"),
            help=self.cm.get_description("magic", "luck")
        )
        async def say_hello_world(ctx):

            rolls, dice_data, reroll = await process_input_dice(ctx, "1d100")
            roll = rolls[0]
            logging.debug(f"Magic Roll: {roll}")
            roll_text = await get_roll_text(ctx, roll, dice_data, reroll, skip_resume=True)

            eff = find_effect(roll.total_dice_result, self.magic_list["magic_luck"])
            await ctx.send(f"{roll_text} \n\n **{eff['description']}**")

            rolls, dice_data, reroll = await process_input_dice(ctx, "1d100")
            roll = rolls[0]
            logging.debug(f"Magic Surge Roll: {roll}")
            roll_text = await get_roll_text(ctx, roll, dice_data, reroll,
                                            skip_resume=True, skip_user_and_dice=True)
            if not eff['surge'] and not eff['fail']:
                return

            if eff['surge']:
                effect = get_magic_surge_effect(roll.total_dice_result,
                                                self.magic_surge_list)
            else:
                effect = get_failed_magic_surge_effect(roll.total_dice_result,
                                                       self.magic_fail_list)
            await ctx.send(
                f"{roll_text} \n\n ||**{effect['description']}**||")

        @bot.command(
            name=self.cm.get_prefix("magic", "surge"),
            help=self.cm.get_description("magic", "surge"))
        async def magic_surge(ctx):
            rolls, dice_data, reroll = await process_input_dice(ctx, "1d100")
            roll = rolls[0]
            logging.debug(f"Magic Surge Roll: {roll}")
            roll_text = await get_roll_text(ctx, roll, dice_data, reroll, skip_resume=True)
            effect = get_magic_surge_effect(roll.total_dice_result, self.magic_surge_list)
            await ctx.send(f"{roll_text} \n\n ||**{effect['description']}**||")


        @bot.command(
            name=self.cm.get_prefix("magic", "surge_type"),
            help=self.cm.get_description("magic", "surge_type")
        )
        async def set_type_surge(ctx, type):
            # Check if type is valid, apply the enum in the magic_surge_type

            if type not in EffectType.__members__:
                await ctx.send(f"Invalid type: {type}")
                return

            global magic_surge_type
            magic_surge_type = EffectType[type].value

            await ctx.send(f"Magic surge type set to: {EffectType[type]}")
