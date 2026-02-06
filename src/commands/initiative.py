import logging
from core.helper import clean_dex
from core.initiative import InitTable
from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text

logger = logging.getLogger(__name__)


def commands_initiative(bot, cm):
    init_items = InitTable()

    @bot.command(
        name=cm.get_prefix("initiative", "roll_initiative"),
        help=cm.get_description("initiative", "roll_initiative"),
    )
    async def roll_initiative(context, initiative: str = "", name: str = "", repeat: int = 1):
        try:
            await initiative_roll(context, initiative, name, repeat)
        except ValueError as e:
            logger.warning(f"Invalid initiative roll parameters: {e}")
            await context.send(
                "Invalid parameters! Try these examples:\n"
                "• `!i 5` - Roll initiative with +5 dex\n"
                "• `!i 3 Goblin` - Roll initiative for 'Goblin' with +3 dex\n"
                "• `!i 2 Kobold 4` - Roll initiative 4 times for 'Kobold' with +2 dex"
            )

    @bot.command(
        name=cm.get_prefix("initiative", "advantage"),
        help=cm.get_description("initiative", "advantage")
    )
    async def roll_initiative_advantage(context, initiative: str = "",
                                        name: str = "", repeat: int = 1):
        try:
            await initiative_roll(context, initiative, name, repeat, adv=True)
        except ValueError as e:
            logger.warning(f"Invalid advantage initiative parameters: {e}")
            await context.send(
                "Invalid parameters! Try these examples:\n"
                "• `!iv 4` - Roll initiative with advantage and +4 dex\n"
                "• `!iv 2 Rogue` - Roll initiative with advantage for 'Rogue' with +2 dex"
            )

    @bot.command(
        name=cm.get_prefix("initiative", "disadvantage"),
        help=cm.get_description("initiative", "disadvantage")
    )
    async def roll_initiative_disadvantage(context, initiative: str = "",
                                           name: str = "", repeat: int = 1):
        try:
            await initiative_roll(context, initiative, name, repeat, adv=False)
        except ValueError as e:
            logger.warning(f"Invalid disadvantage initiative parameters: {e}")
            await context.send(
                "Invalid parameters! Try these examples:\n"
                "• `!id 1` - Roll initiative with disadvantage and +1 dex\n"
                "• `!id -1 Zombie` - Roll initiative with disadvantage for 'Zombie' with -1 dex"
            )

    @bot.command(
        name=cm.get_prefix("initiative", "reset"),
        help=cm.get_description("initiative", "reset")
    )
    async def roll_reset_initiative(context):
        await init_items.reset(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logger.error(f"Error reseting initiative: {e}")

        init_items.initiative_last_msg = await context.send("OK, Initiative table cleared! :)")

    @bot.command(
        name=cm.get_prefix("initiative", "remove"),
        help=cm.get_description("initiative", "remove")
    )
    async def remove_initiative(context, index=0):
        try:
            if index <= 0:
                await context.send(
                    "Please provide a valid index! Example:\n"
                    "• `!iremove 3` - Remove entry #3 from initiative"
                )
                return
            await init_items.remove_index(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                try:
                    await init_items.initiative_last_msg.delete()
                except Exception as e:
                    logger.error(f"Error removing initiative: {e}")

            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except IndexError:
            await context.send(
                f"Index {index} not found in initiative table. Check the table and try again."
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid remove initiative parameters: {e}")
            await context.send(
                "Invalid index! Example:\n"
                "• `!iremove 3` - Remove entry #3 from initiative"
            )
        except Exception as e:
            logger.error(f"Error removing initiative entry: {e}", exc_info=True)
            await context.send("Sorry, I couldn't remove that initiative entry.")

    @bot.command(
        name=cm.get_prefix("initiative", "add_condition"),
        help=cm.get_description("initiative", "add_condition")
    )
    async def add_condition_initiative(context, index: int = 0, args: str = ""):
        try:
            if index <= 0 or not args:
                await context.send(
                    "Please provide both index and condition! Examples:\n"
                    "• `!icond 2 Poisoned` - Add 'Poisoned' condition to entry #2\n"
                    "• `!icond 5 Stunned` - Add 'Stunned' condition to entry #5"
                )
                return
            await init_items.add_condition(context.channel.name, index, args)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()

            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except IndexError:
            await context.send(
                f"Index {index} not found in initiative table. Check the table and try again."
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid add condition parameters: {e}")
            await context.send(
                "Invalid parameters! Examples:\n"
                "• `!icond 2 Poisoned` - Add 'Poisoned' condition to entry #2"
            )
        except Exception as e:
            logger.error(f"Error adding condition: {e}", exc_info=True)
            await context.send("Sorry, I couldn't add that condition. Please check the index and try again.")

    @bot.command(
        name=cm.get_prefix("initiative", "remove_condition"),
        help=cm.get_description("initiative", "remove_condition")
    )
    async def remove_condition_initiative(context, index: int = 0):
        try:
            if index <= 0:
                await context.send(
                    "Please provide a valid index! Example:\n"
                    "• `!icond-remove 2` - Remove condition from entry #2"
                )
                return
            await init_items.remove_condition(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()

            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except IndexError:
            await context.send(
                f"Index {index} not found in initiative table. Check the table and try again."
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid remove condition parameters: {e}")
            await context.send(
                "Invalid index! Example:\n"
                "• `!icond-remove 2` - Remove condition from entry #2"
            )
        except Exception as e:
            logger.error(f"Error removing condition: {e}", exc_info=True)
            await context.send("Sorry, I couldn't remove that condition. Please check the index and try again.")

    @bot.command(
        name=cm.get_prefix("initiative", "next"),
        help=cm.get_description("initiative", "next")
    )
    async def next_initiative(context):
        await init_items.next(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logger.error(f"Error moving initiative: {e}")

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

    @bot.command(
        name=cm.get_prefix("initiative", "previous"),
        help=cm.get_description("initiative", "previous")
    )
    async def prev_initiative(context):
        await init_items.previous(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logger.error(f"Error moving initiative: {e}")

        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

    @bot.command(
        name=cm.get_prefix("initiative", "force"),
        help=cm.get_description("initiative", "force")
    )
    async def force_initiative(context, dice: int = 0, dex: int = 0, args: str = ""):
        try:
            if dice == 0:
                await context.send(
                    "Please provide the dice roll and dex modifier! Examples:\n"
                    "• `!iset 15 3 Fighter` - Set 'Fighter' with roll=15, dex=+3 (total 18)\n"
                    "• `!iset 8 2 Goblin` - Set 'Goblin' with roll=8, dex=+2 (total 10)\n"
                    "• `!iset 12 -1` - Set your character with roll=12, dex=-1 (total 11)"
                )
                return
            dice, _ = await clean_dex(str(dice))
            dex, neg = await clean_dex(str(dex))
            name = f"{args}" if args else context.author.nick

            await init_items.add(context.channel.name, name, dice, str(dex) if not neg else str(dex * -1))
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()

            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid force initiative parameters: {e}")
            await context.send(
                "Invalid parameters! Examples:\n"
                "• `!iset 15 3 Fighter` - Set 'Fighter' with roll=15, dex=+3\n"
                "• `!iset 8 2` - Set your character with roll=8, dex=+2"
            )
        except Exception as e:
            logger.error(f"Error forcing initiative: {e}", exc_info=True)
            await context.send("Sorry, I couldn't force that initiative value. Please check your command and try again.")

    @bot.command(
        name=cm.get_prefix("initiative", "npc_initiative"),
        help=cm.get_description("initiative", "npc_initiative")
    )
    async def npc_initiative(context, *args):
        await npc_initiative_roll(context, args, adv=None)

    @bot.command(
        name=cm.get_prefix("initiative", "npc_advantage"),
        help=cm.get_description("initiative", "npc_advantage")
    )
    async def npc_initiative_advantage(context, *args):
        await npc_initiative_roll(context, args, adv=True)

    @bot.command(
        name=cm.get_prefix("initiative", "npc_disadvantage"),
        help=cm.get_description("initiative", "npc_disadvantage")
    )
    async def npc_initiative_disadvantage(context, *args):
        await npc_initiative_roll(context, args, adv=False)

    async def npc_initiative_roll(context, args, adv=None):
        """
        Roll initiative for multiple NPCs.
        Format: count1 name1 dex1 count2 name2 dex2 ...
        Example: 3 Goblin 2 2 Kobold 1
        """
        try:
            if not args or len(args) < 3:
                mode = "advantage" if adv is True else "disadvantage" if adv is False else "normal"
                await context.send(
                    f"Please provide NPC groups in format: count name dex. Examples:\n"
                    f"• `!npc-init 3 Goblin 2` - Roll initiative for 3 goblins with +2 dex\n"
                    f"• `!npc-init 2 Kobold 1 1 Dragon 3` - 2 kobolds (+1) and 1 dragon (+3)\n"
                    f"• `!npc-iv 5 Guard 0` - 5 guards with advantage\n"
                    f"• `!npc-id 3 Zombie -1` - 3 zombies with disadvantage"
                )
                return

            # Parse arguments in groups of 3: count, name, dex
            npc_groups = []
            i = 0
            while i < len(args):
                if i + 2 >= len(args):
                    await context.send(
                        f"Invalid format. Need groups of 3: count name dex\n"
                        f"Example: `!npc-init 3 Goblin 2 2 Kobold 1`"
                    )
                    return

                try:
                    count = int(args[i])
                    name = str(args[i + 1])
                    dex = str(args[i + 2])
                    npc_groups.append((count, name, dex))
                    i += 3
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid NPC group parameters: {e}")
                    await context.send(
                        f"Invalid format at position {i+1}. Need: count(number) name(text) dex(number)\n"
                        f"Example: `!npc-init 3 Goblin 2`"
                    )
                    return

            # Roll initiative for each NPC group
            channel = context.channel.name
            summary_lines = []
            mode_text = " with advantage" if adv is True else " with disadvantage" if adv is False else ""

            await context.send(f"🎲 Rolling initiative{mode_text} for NPCs...")

            for count, name, dex in npc_groups:
                for i in range(count):
                    # Create unique name for each NPC
                    npc_name = f"{name} {i + 1}" if count > 1 else name

                    # Build dice expression
                    n_die = "1" if adv is None else "2"
                    dice_data = f"{n_die}d20+{dex}"

                    # Roll initiative
                    rolls, dice_data, _ = await process_input_dice(context, dice_data, adv=adv)
                    roll = rolls[0]

                    # Add to initiative table
                    await init_items.add(channel, npc_name, roll.total_dice_result, roll.additional)

                    # Build summary line
                    dice_roll = roll.total_dice_result
                    modifier = roll.additional_eval
                    total = roll.total_roll
                    summary_lines.append(f"• {npc_name}: rolled {dice_roll} + {modifier} = **{total}**")

            # Send summary
            summary = "**Initiative Results:**\n" + "\n".join(summary_lines)
            await context.send(summary)

            # Delete last initiative message and show new table
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()

            init_items.initiative_last_msg = await init_items.show(channel, context)

        except ValueError as e:
            logger.warning(f"Invalid NPC initiative parameters: {e}")
            await context.send(
                "Invalid parameters! Examples:\n"
                "• `!npc-init 3 Goblin 2` - 3 goblins with +2 dex\n"
                "• `!npc-iv 2 Rogue 4` - 2 rogues with advantage"
            )
        except Exception as e:
            logger.error(f"Error rolling NPC initiative: {e}", exc_info=True)
            await context.send("Sorry, I couldn't roll NPC initiative. Please check your command and try again.")

    async def initiative_roll(context, initiative, name, repeat, adv=None):
        try:
            channel = context.channel.name

            if initiative == '' or initiative is None:
                await init_items.show(context.channel.name, context)
                return

            for i in range(0, repeat):
                try:
                    new_name = f"{name}" if name else context.author.nick
                except Exception as e:
                    logger.warning(f"Unable to get name: {e}")
                    new_name = f"{name}" if name else context.author.global_name

                if int(repeat) > 1:
                    new_name = f"{new_name} {i + 1}"

                n_die = "1" if adv is None else "2"
                dice_data = f"{n_die}d20+{initiative}"

                rolls, dice_data, _ = await process_input_dice(context,
                                                               dice_data,
                                                               adv=adv)
                roll = rolls[0]
                if adv is True:
                    await context.send(
                        await get_roll_text(context,
                                            roll,
                                            dice_data,
                                            " for initiative with advantage",
                                            skip_resume=True))
                elif adv is False:
                    await context.send(
                        await get_roll_text(context,
                                            roll,
                                            dice_data,
                                            " for initiative with disadvantage",
                                            skip_resume=True))
                elif rolls[0].amount_of_dice_rolled > 1:
                    await context.send(
                        await get_roll_text(context,
                                            roll,
                                            dice_data,
                                            " for initiative",
                                            skip_resume=True))

                # After send the data
                await init_items.add(channel,
                                     new_name,
                                     roll.total_dice_result,
                                     roll.additional)

            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()

            init_items.initiative_last_msg = await init_items.show(channel,
                                                                   context)

        except Exception as e:
            logger.error(f"Error rolling initiative: {e}", exc_info=True)
            await context.send("Sorry, I couldn't roll initiative. Please check your command and try again.")
