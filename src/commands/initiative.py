from config import initiative_commands
from core.dice_engine import calculate_dice
from core.initiative import InitTable
# from core.roll_view import multiple_d20_text
from utils import clean_dex


def commands_initiative(bot):
    init_items = InitTable()
    @bot.command(
        name=initiative_commands.get("reset"),
        description="Reset the initiative table"
    )
    async def roll_reset_initiative(context):
        await init_items.reset(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                print(f"Error deleting last initiative msg: {e}")
    
        init_items.initiative_last_msg = await context.send("OK, limpei a tabela. Bons dados :)")
    
    
    @bot.command(
        name=initiative_commands.get("remove"),
        description="Remove item from table"
    )
    # @slash_option(
    #     name="index",
    #     description="Initiative position to remove.",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    async def remove_initiative(context, index=0):
        try:
            await init_items.remove_index(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                try:
                    await init_items.initiative_last_msg.delete()
                except Exception as e:
                    print(f"Error deleting last initiative msg: {e}")
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=initiative_commands.get("add_condition"),
        description="Add item from table"
    )
    # @slash_option(
    #     name="index",
    #     description="Initiative position to remove.",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    # @slash_option(
    #     name="args",
    #     description="Condition to add.",
    #     required=True,
    #     opt_type=OptionType.STRING
    # )
    async def add_condition_initiative(context, index: int, args: str = ""):
        try:
            await init_items.add_condition(context.channel.name, index, args)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=initiative_commands.get("remove_condition"),
        description="Remove item from table"
    )
    # @slash_option(
    #     name="index",
    #     description="Initiative position to remove.",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    async def remove_condition_initiative(context, index: int):
        try:
            await init_items.remove_condition(context.channel.name, index)
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
        except Exception as e:
            await context.send(f"Exception {e}")
    
    @bot.command(
        name=initiative_commands.get("default"),
        description="Roll initiative!"
    )
    # @slash_option(
    #     name="initiative",
    #     description="Character initiative modifier. E.g: 2",
    #     required=False,
    #     opt_type=OptionType.INTEGER
    # )
    # @slash_option(
    #     name="name",
    #     description="Character name. Default is the user name.",
    #     required=False,
    #     opt_type=OptionType.STRING
    # )
    # @slash_option(
    #     name="repeat",
    #     description="Number of times that the roll will be repeated. Default is 1.",
    #     required=False,
    #     opt_type=OptionType.INTEGER
    # )
    async def roll_initiative(context, initiative: int = -99, name: str = "", repeat: int = 1):
        try:
            channel = context.channel.name
    
            if initiative == -99:
                print("Show init table")
                await init_items.show(context.channel.name, context)
                return
    
            for i in range(0, repeat):
                try:
                    new_name = f"{name}" if name else context.author.nick
                except:
                    new_name = f"{name}" if name else context.author.global_name
    
                if int(repeat) > 1:
                    new_name = f"{new_name} {i+1}"
    
                dice = await calculate_dice(context, [[1, 20]], [], str(initiative))
                await init_items.add(channel, new_name, dice['only_dice'], str(initiative))
    
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(channel, context)
    
        except Exception as e:
            raise
            print(context.send(f"Erro: {e}"))
    
    @bot.command(
        name=initiative_commands.get("next"),
        description="Move the initiative to the next character."
    )
    async def next_initiative(context):
        await init_items.next(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            try:
                await init_items.initiative_last_msg.delete()
            except Exception as e:
                print(f"Error deleting last initiative msg: {e}")
    
        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    
    
    @bot.command(
        name=initiative_commands.get("previous"),
        description="Move the initiative to the previous character."
    )
    async def prev_initiative(context):
        await init_items.previous(context.channel.name)
        # Delete last msg and send the new one
        if init_items.initiative_last_msg:
            await init_items.initiative_last_msg.delete()
    
        init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    
    
    @bot.command(
        name=initiative_commands.get("advantage"),
        description="Roll initiative with advantage!"
    )
    # @slash_option(
    #     name="dex",
    #     description="Character dexterity modifier. E.g: 2",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    # @slash_option(
    #     name="args",
    #     description="Character name. Default is the user name.",
    #     required=True,
    #     opt_type=OptionType.STRING
    # )
    async def roll_initiative_advantage(context, dex: int = 0, args: str = ""):
        try:
            if not dex:
                await init_items.show(context.channel.name, context)
                return
    
            name = f"{args}" if args else context.author.nick
    
            dice = await calculate_dice(context, [[2, 20]], [], str(dex))
    
            text = await multiple_d20_text(context, dice, None)
            await context.send(text)
            await init_items.add(context.channel.name, name, dice['result_die'][0].larger(), str(dex))
    
            # Delete last msg and send the new one
            if init_items.initiative_last_msg:
                await init_items.initiative_last_msg.delete()
    
            init_items.initiative_last_msg = await init_items.show(context.channel.name, context)
    
        except Exception as e:
            await context.send(f"Exception {e}")
    
    
    @bot.command(
        name=initiative_commands.get("force"),
        description="Force initiative. Add a character that already rolled dice into initiative table."
    )
    # @slash_option(
    #     name="dice",
    #     description="Dice rolled for initiative.",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    # @slash_option(
    #     name="dex",
    #     description="Character dexterity modifier",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    # @slash_option(
    #     name="args",
    #     description="Character name.",
    #     required=True,
    #     opt_type=OptionType.STRING
    # )
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
            await context.send(f"Exception {e}")
