import logging
from core.helper import clean_dex
from core.initiative import InitTable
from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text

logger = logging.getLogger(__name__)


def commands_initiative(bot, config_manager):

    init_items = InitTable()

    @bot.command(
        name=config_manager.get_prefix("initiative", "default"),
        description="Roll initiative!"
    )
    async def roll_initiative(context, initiative: str = "", name: str = "", repeat: int = 1):
        await initiative_roll(context, initiative, name, repeat)

    @bot.command(
        name=config_manager.get_prefix("initiative", "advantage"),
        description="Roll initiative with advantage!"
    )
    async def roll_initiative_advantage(context, initiative: str = "",
                                        name: str = "", repeat: int = 1):
        await initiative_roll(context, initiative, name, repeat, adv=True)

    @bot.command(
        name=config_manager.get_prefix("initiative", "reset"),
        description="Reset the initiative table"
    )
    async def roll_reset_initiative(context):
        await init_items.reset(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logging.error(f"Error reseting initiative: {e}")
    
        init_items.initiative_last_msg = await context.send("OK, Initiative table cleared! :)")


    @bot.command(
        name=config_manager.get_prefix("initiative", "remove"),
        description="Remove item from table"
    )
    async def remove_initiative(context, index=0):
        try:
            await init_items.remove_index(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                try:
                    await init_items.initiative_last_msg.delete()
                except Exception as e:
                    logging.error(f"Error removing initiative: {e}")
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=config_manager.get_prefix("initiative", "add_condition"),
        description="Add item from table"
    )
    async def add_condition_initiative(context, index: int, args: str = ""):
        try:
            await init_items.add_condition(context.channel.name, index, args)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            logging.error(f"Error adding condition: {e}")
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=config_manager.get_prefix("initiative", "remove_condition"),
        description="Remove item from table"
    )
    async def remove_condition_initiative(context, index: int):
        try:
            await init_items.remove_condition(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            logging.error(f"Error removing condition: {e}")
            await context.send(f"Exception {e}")


    @bot.command(
        name=config_manager.get_prefix("initiative", "next"),
        description="Move the initiative to the next character."
    )
    async def next_initiative(context):
        await init_items.next(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logging.error(f"Error moving initiative: {e}")
    
        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    
    
    @bot.command(
        name=config_manager.get_prefix("initiative", "previous"),
        description="Move the initiative to the previous character."
    )
    async def prev_initiative(context):
        await init_items.previous(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                logging.error(f"Error moving initiative: {e}")
    
        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)

    @bot.command(
        name=config_manager.get_prefix("initiative", "force"),
        description="Add manually initiative"
    )
    async def force_initiative(context, dice: int = 0, dex: int = 0, args: str = ""):
        try:
            dice, _ = await clean_dex(str(dice))
            dex, neg = await clean_dex(str(dex))
            name = f"{args}" if args else context.author.nick
    
            await init_items.add(context.channel.name, name, dice, str(dex) if not neg else str(dex * -1))
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    
        except Exception as e:
            logging.error(f"Error forcing initiative: {e}")
            await context.send(f"Exception {e}")


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
                    logging.warning(f"Unable to get name: {e}")
                    new_name = f"{name}" if name else context.author.global_name

                if int(repeat) > 1:
                    new_name = f"{new_name} {i + 1}"

                n_die = "1" if not adv else "2"
                dice_data = f"{n_die}d20+{initiative}"

                rolls, dice_data, _ = await process_input_dice(context,
                                                               dice_data,
                                                               adv=adv)
                roll = rolls[0]
                if adv:
                    await context.send(
                        await get_roll_text(context,
                                            roll,
                                            dice_data,
                                            " for initiative with advantage",
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
            logging.error(f"Error rolling initiative: {e}")
            await context.send(f"Exception {e}")
