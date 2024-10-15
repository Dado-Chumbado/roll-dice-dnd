import re


def format_commands(config_manager):
    """Formats the commands from the configuration for displaying in the help message"""
    help_text = "Here are the available commands:\n\n"

    for category, category_commands in config_manager.config.items():
        help_text += f"**{category.capitalize()} Commands:**\n"
        for command_name, command_info in category_commands.items():
            alias = command_info.get("alias")
            description = command_info.get("description",
                                           "No description available")
            help_text += f"  - {command_name.replace('_', ' ').capitalize()}: `{alias}` - {description}\n"
        help_text += "\n"

    return help_text

async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative