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

    if os.getenv("sentry_dsn"):
        import sentry_sdk
        sentry_sdk.init(
            dsn=os.getenv("sentry_dsn"),
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=os.getenv("traces_sample_rate", 1.0),
            enable_tracing=True,

        )

        # Manually call start_profiling and stop_profiling
        # to profile the code in between
        sentry_sdk.profiler.start_profiler()
        # do some work here
        sentry_sdk.profiler.stop_profiler()

    # Setup logging configuration
    setup_logging()

    # Set up the discord bot
    COMMAND_CHAR = os.getenv("command_char")
    intents = discord.Intents.default()
    intents.message_content = True

    # Load the command configuration
    config_manager = ConfigManager()

    # Load and prepare DB
    from db.models import setup_db
    setup_db()

    # Create a bot instance
    bot = commands.Bot(command_prefix=COMMAND_CHAR, intents=intents)

    commands_setup(bot, config_manager)

    bot.run(os.getenv("discord_token"))
