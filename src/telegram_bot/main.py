"""Entry point for the Telegram dice bot."""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram_bot.bot import create_telegram_bot


def main():
    """Load environment and start the Telegram bot."""
    # Load from src/.env regardless of the working directory
    dotenv_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path)
    logger.info(f"Loading .env from {dotenv_path} (exists={dotenv_path.exists()})")

    token = os.getenv("telegram_token")
    logger.info(f"D20_IRL_ENABLED={os.getenv('D20_IRL_ENABLED')} D20_IRL_URL={os.getenv('D20_IRL_URL')} D20_IRL_USERNAME={os.getenv('D20_IRL_USERNAME')}")

    if not token:
        raise ValueError("telegram_token not found in environment variables")

    app = create_telegram_bot(token)
    print("Telegram bot started. Press Ctrl+C to stop.")
    # drop_pending_updates=True clears any stale getUpdates session left by a
    # previous instance (prevents HTTP 409 Conflict on restart).
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
