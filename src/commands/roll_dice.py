import logging

from core.dice_engine import process_input_dice
from core.helper import send_message
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
                logger.debug(f"Roll: {roll}")
                response = await get_roll_text(ctx, roll, dice_data, reroll)
                await send_message(ctx, response)
        except ValueError as e:
            logger.warning(f"Invalid dice expression: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!r` or `!r d20` - Roll a d20\n"
                "• `!r 2d6+5` - Roll 2d6 and add 5\n"
                "• `!r 3d8-1d4+2` - Roll multiple dice with modifiers\n"
                "• `!r 4d6r1` - Roll 4d6 and reroll any 1s"
            )
        except Exception as e:
            logger.error(f"Error processing dice roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't process that dice roll. Please try again.")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "dm_roll"),
        help=cm.get_description("roll", "dm_roll")
    )
    async def command_roll_dm_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data)
            for roll in rolls:
                logger.debug(f"Roll dm: {roll}")
                await ctx.author.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except ValueError as e:
            logger.warning(f"Invalid dice expression for DM roll: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!dm d20+3` - Roll a d20+3 (sent to your DM)\n"
                "• `!dm 4d6` - Roll 4d6 (sent to your DM)"
            )
        except Exception as e:
            logger.error(f"Error processing DM dice roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't send that roll to your DM. Please check your syntax and try again.")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "critical_damage"),
        help=cm.get_description("roll", "critical_damage")
    )
    async def command_roll_critical_damage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command)
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, critical=True)
            for roll in rolls:
                logger.debug(f"Roll critical damage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except ValueError as e:
            logger.warning(f"Invalid dice expression for critical damage: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!critic d8+5` - Critical with 1d8+5 (doubles to 2d8, maxes first die)\n"
                "• `!critic 2d6+3` - Critical with 2d6+3 (doubles to 4d6+3)"
            )
        except Exception as e:
            logger.error(f"Error processing critical damage roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't process that critical damage roll. Please try again.")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "advantage"),
        help=cm.get_description("roll", "advantage")
    )
    async def command_roll_advantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=True)
            for roll in rolls:
                logger.debug(f"Roll advantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except ValueError as e:
            logger.warning(f"Invalid dice expression for advantage: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!v` or `!v 5` - Roll 2d20+5 with advantage\n"
                "• `!v d4+2` - Roll 2d20+1d4+2 with advantage\n"
                "• `!v -3` - Roll 2d20-3 with advantage"
            )
        except Exception as e:
            logger.error(f"Error processing advantage roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't process that advantage roll. Please try again.")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "double_advantage"),
        help=cm.get_description("roll", "double_advantage")
    )
    async def command_roll_double_advantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=True, double_adv=True)
            for roll in rolls:
                logger.debug(f"Roll double advantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except ValueError as e:
            logger.warning(f"Invalid dice expression for double advantage: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!vv` or `!vv 3` - Roll 3d20+3 with double advantage\n"
                "• `!vv d6+1` - Roll 3d20+1d6+1 with double advantage"
            )
        except Exception as e:
            logger.error(f"Error processing double advantage roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't process that double advantage roll. Please try again.")


    @bot.hybrid_command(
        name=cm.get_prefix("roll", "disadvantage"),
        help=cm.get_description("roll", "disadvantage")
    )
    async def command_roll_disadvantage_dice(ctx, *, command=None):
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(ctx, dice_data, adv=False)
            for roll in rolls:
                logger.debug(f"Roll disadvantage: {roll}")
                await ctx.send(await get_roll_text(ctx, roll, dice_data, reroll))
        except ValueError as e:
            logger.warning(f"Invalid dice expression for disadvantage: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!d` or `!d 2` - Roll 2d20+2 with disadvantage\n"
                "• `!d d8-1` - Roll 2d20+1d8-1 with disadvantage"
            )
        except Exception as e:
            logger.error(f"Error processing disadvantage roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't process that disadvantage roll. Please try again.")
