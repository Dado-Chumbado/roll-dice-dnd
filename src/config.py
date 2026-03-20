import json
import logging
import os

logger = logging.getLogger(__name__)


def _load_config(config_file_path):
    """
    Load the configuration from the specified JSON file.
    """
    try:
        with open(config_file_path, 'r') as file:
            logger.debug(f"Loading config from {config_file_path}")
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Config file {config_file_path} not found.")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        raise


class ConfigManager:
    def __init__(self, config_file_path='src/config.json'):
        """
        Initialize the ConfigManager with the path to the config file and load the config.
        """
        self.config = _load_config(config_file_path)

    def get_prefix(self, category, command):
        """
        Retrieves the alias (prefix) for a command from the specified category.
        Env var DISCORD_CMD_{CATEGORY}_{COMMAND} (uppercased) takes precedence over config.json.

        :param category: The command category (e.g., 'roll', 'initiative', 'stats')
        :param command: The specific command within the category (e.g., 'default', 'advantage')
        :return: The alias (prefix) for the command.
        :raises KeyError: If the category or command is not found.
        """
        env_key = f"DISCORD_CMD_{category}_{command}".upper()
        env_val = os.getenv(env_key, "").strip()
        if env_val:
            logger.debug(f"Prefix for {category}/{command} overridden by env {env_key}={env_val}")
            return env_val

        try:
            logger.debug(f"Fetching prefix for category: {category}, command: {command}")
            return self.config[category][command]['alias']
        except KeyError as e:
            logger.error(f"KeyError: {e}")
            raise KeyError(f"'{command}' not found in '{category}' category") from e

    def get_description(self, category, command):
        """
        Retrieves the description for a command from the specified category.

        :param category: The command category (e.g., 'roll', 'initiative', 'stats')
        :param command: The specific command within the category (e.g., 'default', 'advantage')
        :return: The description for the command.
        :raises KeyError: If the category or command is not found.
        """
        try:
            return self.config[category][command]['description']
        except KeyError as e:
            logger.error(f"KeyError: {e}")
            raise KeyError(f"'{command}' not found in '{category}' category") from e
