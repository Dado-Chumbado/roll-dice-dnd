import os
import json

# Load config from json file
# Load the correct path from config.json file
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file) as config_file:
    config = json.load(config_file)

# Grouped constants access
roll_commands = config["roll"]
initiative_commands = config["initiative"]
stats_commands = config["stats"]
dice_commands = config["dice"]
