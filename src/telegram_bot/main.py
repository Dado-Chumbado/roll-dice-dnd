"""Entry point for the Telegram dice bot."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram_bot.bot import create_telegram_bot


def main():
    """Load environment and start the Telegram bot."""
    load_dotenv()
    token = os.getenv("telegram_token")

    if not token:
        raise ValueError("telegram_token not found in environment variables")

    app = create_telegram_bot(token)
    print("Telegram bot started. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
