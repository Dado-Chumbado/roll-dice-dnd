#!/usr/bin/env python3

import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from commands import commands_setup
from config import ConfigManager
from logger import setup_logging


if __name__ == "__main__":
    load_dotenv()

    # Setup logging configuration
    setup_logging()

    # Set up the discord bot
    COMMAND_CHAR = os.getenv("command_char")
    intents = discord.Intents.default()
    intents.message_content = True

    # Load the command configuration
    config_manager = ConfigManager()

    # Create a bot instance
    bot = commands.Bot(command_prefix=COMMAND_CHAR, intents=intents)

    commands_setup(bot, config_manager)

    bot.run(os.getenv("discord_token"))
