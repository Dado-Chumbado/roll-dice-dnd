import os
import json
import logging
from slugify import slugify

logger = logging.getLogger(__name__)

ROOT_DATA = os.path.join(os.getcwd(), 'data/')


class DMManager:
    """Manages DM (Dungeon Master) assignments per channel."""

    def __init__(self, path=ROOT_DATA):
        self.path = path
        self.dm_file = os.path.join(path, 'dm_settings.json')
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the DM settings file if it doesn't exist."""
        os.makedirs(self.path, exist_ok=True)
        if not os.path.exists(self.dm_file):
            with open(self.dm_file, 'w') as f:
                json.dump({}, f)

    def set_dm(self, channel_name: str, user_id: int, username: str):
        """
        Set the DM for a specific channel.

        Args:
            channel_name: Name of the Discord channel
            user_id: Discord user ID of the DM
            username: Display name of the DM
        """
        data = self._load_data()
        channel_key = slugify(channel_name)

        data[channel_key] = {
            'user_id': user_id,
            'username': username
        }

        self._save_data(data)
        logger.info(f"Set DM for channel '{channel_name}': {username} (ID: {user_id})")

    def get_dm(self, channel_name: str):
        """
        Get the DM for a specific channel.

        Args:
            channel_name: Name of the Discord channel

        Returns:
            dict with 'user_id' and 'username' or None if no DM set
        """
        data = self._load_data()
        channel_key = slugify(channel_name)
        return data.get(channel_key)

    def remove_dm(self, channel_name: str):
        """
        Remove the DM setting for a specific channel.

        Args:
            channel_name: Name of the Discord channel
        """
        data = self._load_data()
        channel_key = slugify(channel_name)

        if channel_key in data:
            del data[channel_key]
            self._save_data(data)
            logger.info(f"Removed DM for channel '{channel_name}'")
            return True
        return False

    def _load_data(self):
        """Load DM settings from file."""
        try:
            with open(self.dm_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_data(self, data):
        """Save DM settings to file."""
        with open(self.dm_file, 'w') as f:
            json.dump(data, f, indent=2)


# Global instance
dm_manager = DMManager()
