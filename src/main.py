#!/usr/bin/env python3

import os
from interactions import Client, Intents, listen
from dotenv import load_dotenv


load_dotenv()
STATS_ENABLE = os.getenv("save_stats_db")
COMMAND_CHAR = os.getenv("command_char")


bot = Client(command_prefix=[COMMAND_CHAR],
             description="Roll dice and control initiative table",
             intents=Intents.DEFAULT)

from commands.commands import *


@listen()
async def on_ready():
    print(f"I'm logged in as {bot.user.display_name} !\n Statistics enable: {STATS_ENABLE}.")


bot.start(os.getenv("discord_token"))
