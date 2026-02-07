import logging

from core.dice_engine import process_input_dice
from core.helper import send_message
from core.roll_view import get_roll_text
from core.dm_manager import dm_manager

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


    async def dm_roll_helper(ctx, command, adv=None):
        """Helper function for DM rolls with optional advantage/disadvantage."""
        try:
            dice_data = ''.join(command) if command else 'd20'
            rolls, dice_data, reroll = await process_input_dice(ctx, dice_data, adv=adv)

            # Get the DM for this channel
            dm_info = dm_manager.get_dm(ctx.channel.name)

            # Build roll text with advantage/disadvantage label
            mode_text = ""
            if adv is True:
                mode_text = " with advantage"
            elif adv is False:
                mode_text = " with disadvantage"

            if dm_info:
                # Send to the DM
                try:
                    dm_user = await bot.fetch_user(dm_info['user_id'])
                    for roll in rolls:
                        logger.debug(f"Roll dm{mode_text}: {roll}")
                        roll_text = await get_roll_text(ctx, roll, dice_data, reroll)
                        # Add context about who rolled
                        message = f"**Secret roll{mode_text} from {ctx.author.display_name} in #{ctx.channel.name}:**\n{roll_text}"
                        await dm_user.send(message)

                    # Confirm to the player
                    await ctx.send(f"🎲 Roll{mode_text} sent to DM ({dm_info['username']})!", delete_after=5)
                except Exception as e:
                    logger.error(f"Error sending to DM: {e}")
                    await ctx.send(
                        f"❌ Couldn't send to DM {dm_info['username']}. They may have DMs disabled.\n"
                        f"Sending to your DMs instead..."
                    )
                    # Fallback to sending to player
                    for roll in rolls:
                        await ctx.author.send(await get_roll_text(ctx, roll, dice_data, reroll))
            else:
                # No DM set, send to player's own DMs (legacy behavior)
                for roll in rolls:
                    logger.debug(f"Roll dm{mode_text}: {roll}")
                    await ctx.author.send(await get_roll_text(ctx, roll, dice_data, reroll))

                await ctx.send(
                    f"ℹ️ No DM set for this channel. Roll{mode_text} sent to your DMs.\n"
                    "Tip: Use `!set-dm @username` to set a DM for this channel.",
                    delete_after=10
                )

        except ValueError as e:
            logger.warning(f"Invalid dice expression for DM roll: {e}")
            await ctx.send(
                "Invalid dice expression! Try these examples:\n"
                "• `!dm d20+3` - Roll a d20+3 (sent to DM)\n"
                "• `!dm 4d6` - Roll 4d6 (sent to DM)\n"
                "• `!dm-v d20+5` - Roll with advantage (sent to DM)\n"
                "• `!dm-d d20+2` - Roll with disadvantage (sent to DM)"
            )
        except Exception as e:
            logger.error(f"Error processing DM dice roll: {e}", exc_info=True)
            await ctx.send("Sorry, I couldn't send that roll. Please check your syntax and try again.")

    @bot.hybrid_command(
        name=cm.get_prefix("roll", "dm_roll"),
        help=cm.get_description("roll", "dm_roll")
    )
    async def command_roll_dm_dice(ctx, *, command=None):
        await dm_roll_helper(ctx, command, adv=None)

    @bot.hybrid_command(
        name=cm.get_prefix("roll", "dm_advantage"),
        help=cm.get_description("roll", "dm_advantage")
    )
    async def command_roll_dm_advantage(ctx, *, command=None):
        await dm_roll_helper(ctx, command, adv=True)

    @bot.hybrid_command(
        name=cm.get_prefix("roll", "dm_disadvantage"),
        help=cm.get_description("roll", "dm_disadvantage")
    )
    async def command_roll_dm_disadvantage(ctx, *, command=None):
        await dm_roll_helper(ctx, command, adv=False)


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
