import re
import json
from plugin_manager import get_plugins_commands


def format_commands(source):
    """Formats commands from the source (config or plugins) for displaying in the help message."""
    help_text = ""
    for category, category_commands in source:
        help_text += f" - {category.capitalize()} \n"
        for command_name, command_info in category_commands.items():
            alias = command_info.get("alias")
            description = command_info.get("description", "No description available")
            help_text += f"  - {command_name.replace('_', ' ').capitalize()}: `{alias}` - {description}\n"
    return help_text


def format_plugin_commands():
    """Gets the commands from the plugins."""
    help_text = ""
    for plugin in get_plugins_commands():
        with open(plugin) as f:
            plugin_config = json.load(f)
            help_text += format_commands(plugin_config.items())

    return help_text

async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative


async def send_message(ctx, message):
    '''Send a message to the channel respecting the message limit of 2000 characters
    
    Args:
        ctx: Context of the message
        message: Message to send
    '''

    if len(message) > 2000:

        for i in range(0, len(message), 2000):
            await ctx.send(message[i:i+2000])
    else:
        await ctx.send(message)