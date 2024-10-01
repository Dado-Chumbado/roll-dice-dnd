import logging

from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text

logger = logging.getLogger(__name__)


def commands_dice(bot, config_manager):

    @bot.command(name=config_manager.get_prefix("roll", "default"), description="Roll dice")
    async def command_roll_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data)
            for roll in rolls:
                logging.debug(f"Roll: {roll}")
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")

    @bot.command(
        name=config_manager.get_prefix("roll", "dm_roll"),
        description="Roll private dice"
    )
    async def command_roll_dm_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data)
            for roll in rolls:
                logging.debug(f"Roll dm: {roll}")
                await context.author.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")

    @bot.command(
        name=config_manager.get_prefix("roll", "critical_damage"),
        description="Roll critical damage dice"
    )
    async def command_roll_critical_damage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, critical=True)
            for roll in rolls:
                logging.debug(f"Roll critical damage: {roll}")
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")


    @bot.command(
        name=config_manager.get_prefix("roll", "advantage"),
        description="Roll dice with advantage"
    )
    async def command_roll_advantage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=True)
            for roll in rolls:
                logging.debug(f"Roll advantage: {roll}")
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")

    @bot.command(
        name=config_manager.get_prefix("roll", "double_advantage"),
        description="Roll dice with double advantage"
    )
    async def command_roll_double_advantage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=True, double_adv=True)
            for roll in rolls:
                logging.debug(f"Roll double advantage: {roll}")
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")

    @bot.command(
        name=config_manager.get_prefix("roll", "disadvantage"),
        description="Roll dice with disadvantage"
    )
    async def command_roll_disadvantage_dice(context, args: str = ""):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=False)
            for roll in rolls:
                logging.debug(f"Roll disadvantage: {roll}")
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await context.send(f"Exception {e}")