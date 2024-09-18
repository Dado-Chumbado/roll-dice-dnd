from config import dice_commands
from core.save_dice import DiceTable


def commands_storage(bot):
    @bot.command(
        name=dice_commands.get("save"),
        description="Save dice roll. E.g: 1d6+2"
    )
    # @slash_option(
    #     name="name",
    #     description="Dice save name. E.g: Machado",
    #     required=True,
    #     opt_type=OptionType.STRING
    # )
    # @slash_option(
    #     name="args",
    #     description="Dice values to save. E.g: 1d6+2",
    #     required=True,
    #     opt_type=OptionType.STRING
    # )
    async def save_dice(context,  name: str, args: str,):
        try:
            dice_items = DiceTable(context.author.id)
            await dice_items.add(name, args)
            await dice_items.show(context)
    
        except Exception as e:
            await context.send(f"Erro: {e}")
    
    
    @bot.command(
        name=dice_commands.get("list"),
        description="List saved dice."
    )
    async def list_saved_dice(context):
        try:
            dice_items = DiceTable(context.author.id)
            await dice_items.show(context)
    
        except Exception as e:
            await context.send(f"Erro: {e}")
    
    
    @bot.command(
        name=dice_commands.get("remove"),
        description="Remove saved dice by index."
    )
    # @slash_option(
    #     name="index",
    #     description="Dice index to remove. E.g: 1",
    #     required=True,
    #     opt_type=OptionType.INTEGER
    # )
    async def remove_dice(context, index: int):
        try:
            dice_items = DiceTable(context.author.id)
            await dice_items.remove_index(index)
            await dice_items.show(context)
    
        except Exception as e:
            await context.send(f"Erro: {e}")
    
    
    @bot.command(
        name=dice_commands.get("reset"),
        description="Remove all saved dice."
    )
    async def reset_dice(context):
        try:
            dice_items = DiceTable(context.author.id)
            await dice_items.reset()
            await dice_items.show(context)
    
        except Exception as e:
            await context.send(f"Erro: {e}")