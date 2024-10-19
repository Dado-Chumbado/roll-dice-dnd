import logging

from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text

logger = logging.getLogger(__name__)


def commands_dice(bot, cm):
    @bot.hybrid_command(name=cm.get_prefix("roll", "roll_dice"),
                        help=cm.get_description("roll", "roll_dice"))
    async def command_roll_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data)
            for roll in rolls:
                logging.debug(f"Roll: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "dm_roll"),
        help=cm.get_description("roll", "dm_roll")
    )
    async def command_roll_dm_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data)
            for roll in rolls:
                logging.debug(f"Roll dm: {roll}")
                await ctx.author.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "critical_damage"),
        help=cm.get_description("roll", "critical_damage")
    )
    async def command_roll_critical_damage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command)
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, critical=True)
            for roll in rolls:
                logging.debug(f"Roll critical damage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "advantage"),
        help=cm.get_description("roll", "advantage")
    )
    async def command_roll_advantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=True)
            for roll in rolls:
                logging.debug(f"Roll advantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "double_advantage"),
        help=cm.get_description("roll", "double_advantage")
    )
    async def command_roll_double_advantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=True, double_adv=True)
            for roll in rolls:
                logging.debug(f"Roll double advantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "disadvantage"),
        help=cm.get_description("roll", "disadvantage")
    )
    async def command_roll_disadvantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=False)
            for roll in rolls:
                logging.debug(f"Roll disadvantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except Exception as e:
            logging.error(f"Error processing dice: {e}")
            await ctx.send(f"Exception {e}")
