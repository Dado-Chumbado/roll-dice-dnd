from config import roll_commands
from core.dice_engine import process_input_dice
from core.save_dice import DiceTable
from core.roll_view import multiple_d20_text, get_roll_text



def commands_dice(bot):

    @bot.command(name=roll_commands.get("default"), description="Roll dice")
    async def command_roll_dice(context, args: str = "d20"):
        try:
            dice_data = ''.join(args)
            rolls = await process_input_dice(context, dice_data)
            await context.send(f"{rolls[0].dice_expression} => {rolls[0].total_roll}")

        except Exception as e:
            raise


    # @bot.command(
    #     name=roll_commands.get("dm_roll"),
    #     description="Roll private dice"
    # )
    # async def command_roll_dm_dice(context, args: str = "d20"):
    #     try:
    #         '''
    #             process("1d10+1d4-1")
    #             (['1d10 = [3]', '1d4 = [2]'], 4)
    #         '''
    #         rr = None
    #         data = ''.join(args)
    #         if not data:
    #             data = "d20"
    #         if data[-2:] in ["r1", "r2", "r3"]:
    #             rr = data[-2:]
    #             data = data.split(data[-2:])[0]
    #
    #         for index, dice in enumerate(await process(context, data, ignore_d20=False, reroll=rr)):  # Parse and roll dice
    #             text, result_text, msg_result = await get_roll_text(context, dice, True if index == 0 else False)
    #             await context.author.send(f"{text}\n\n{result_text}{msg_result}")
    #
    #         await context.send(f"Rolagem enviada para {context.author.nick}")
    #     except Exception as e:
    #         await context.send(f"Exception {e}")
    #
    #
    # @bot.command(
    #     name=roll_commands.get("critical_damage"),
    #     description="Roll critical damage dice"
    # )
    # async def command_roll_critical_damage_dice(context, args: str, extra: str = ""):
    #     try:
    #         rr = None
    #         data = ''.join(args)
    #
    #         extra_text = ""
    #         # Check if is a dice saved
    #         dice_saved = None
    #         try:
    #             dice = DiceTable(context.author.id)
    #             dice_saved = await dice.get(data)
    #         except Exception as e:
    #             print(f"Error: {e}")
    #             pass
    #
    #         if extra != "":
    #             extra = f"+{extra}"
    #
    #         if dice_saved:
    #             data = dice_saved + extra
    #             extra_text = f"\n## Rolando {args}: {data} \n\n\n"
    #         else:
    #             data += extra
    #
    #         if data[-2:] in ["r1", "r2", "r3"]:
    #             rr = data[-2:]
    #             data = data.split(data[-2:])[0]
    #
    #         for index, dice_list in enumerate(
    #                 await process(context, data, ignore_d20=False, reroll=rr, critical=True)):  # Parse and roll dice
    #             text, result_text, msg_result = await get_roll_text(context, dice_list, True if index == 0 else False)
    #             await context.send(f"{extra_text}{text}\n\n{result_text}{msg_result}")
    #
    #     except Exception as e:
    #         await context.send(f"Exception {e}")
    #
    #
    # @bot.command(
    #     name=roll_commands.get("advantage"),
    #     description="Roll dice with advantage"
    # )
    # async def command_roll_advantage_dice(context, args: str = ""):
    #     try:
    #         data = ''.join(args)
    #         # Clean up
    #         if data == "d20":
    #             data = ""
    #         data = data.replace("d20", "")
    #
    #
    #         dice = await calculate_dice(context, [[2, 20]], [], None, adv=True)
    #         text = ""
    #         try:
    #             # Try to evaluate extra data
    #             additional_dice = await process(context, data, ignore_d20=True)
    #             text = await multiple_d20_text(context, dice, additional_dice)
    #         except Exception as e:
    #             print(e)
    #
    #         if text:
    #             await context.send(text)
    #
    #     except Exception as e:
    #         raise
    #         await context.send(f"Exception {e}")
    #
    #
    # @bot.command(
    #     name=roll_commands.get("double_advantage"),
    #     description="Roll dice with double advantage"
    # )
    # async def command_roll_double_advantage_dice(context, args: str = ""):
    #     try:
    #         data = ''.join(args)
    #         # Clean up
    #         if data == "d20" or data == "1d20":
    #             data = ""
    #         data = data.replace("1d20", "").replace("d20", "")
    #
    #
    #         dice = await calculate_dice(context, [[3, 20]], [], None, adv=True)
    #         try:
    #             # Try to evaluate extra data
    #             additional_dice = await process(context, data, ignore_d20=True)
    #             text = await multiple_d20_text(context, dice, additional_dice)
    #         except:
    #             pass
    #
    #         if text:
    #             await context.send(text)
    #     except Exception as e:
    #         await context.send(f"Exception {e}")
    #
    #
    # @bot.command(
    #     name=roll_commands.get("disadvantage"),
    #     description="Roll dice with disadvantage"
    # )
    # async def command_roll_disadvantage_dice(context, args: str = ""):
    #     try:
    #         data = ''.join(args)
    #         # SANITIZE STRING -> MOVE THIS
    #         if data == "d20" or data == "1d20":
    #             data = ""
    #         data = data.replace("1d20", "").replace("d20", "")
    #
    #
    #         dice = await calculate_dice(context, [[2, 20]], [], None, adv=False)
    #         try:
    #             # Try to evaluate extra data
    #             additional_dice = await process(context, data, ignore_d20=True)
    #             text = await multiple_d20_text(context, dice, additional_dice)
    #         except Exception as e:
    #             await context.send(f"Exception {e}")
    #
    #         if text:
    #             await context.send(text)
    #     except Exception as e:
    #         await context.send(f"Exception {e}")
