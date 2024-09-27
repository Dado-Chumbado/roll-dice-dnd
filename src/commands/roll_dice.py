from config import roll_commands
from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text # multiple_d20_text,


def commands_dice(bot):

    @bot.command(name=roll_commands.get("default"), description="Roll dice")
    async def command_roll_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data)
            for roll in rolls:
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise

    @bot.command(
        name=roll_commands.get("dm_roll"),
        description="Roll private dice"
    )
    async def command_roll_dm_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data)
            for roll in rolls:
                await context.author.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise

    @bot.command(
        name=roll_commands.get("critical_damage"),
        description="Roll critical damage dice"
    )
    async def command_roll_critical_damage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, critical=True)
            for roll in rolls:
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise


    @bot.command(
        name=roll_commands.get("advantage"),
        description="Roll dice with advantage"
    )
    async def command_roll_advantage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=True)
            for roll in rolls:
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise

    @bot.command(
        name=roll_commands.get("double_advantage"),
        description="Roll dice with double advantage"
    )
    async def command_roll_double_advantage_dice(context, *args):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=True, double_adv=True)
            for roll in rolls:
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise

    @bot.command(
        name=roll_commands.get("disadvantage"),
        description="Roll dice with disadvantage"
    )
    async def command_roll_disadvantage_dice(context, args: str = ""):
        try:
            dice_data = ''.join(args) if args else 'd20'
            rolls, dice_data, reroll  = await process_input_dice(context, dice_data, adv=False)
            for roll in rolls:
                await context.send(await get_roll_text(context, roll, dice_data, reroll))
        except Exception as e:
            raise