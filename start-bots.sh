#!/bin/bash

# Start both Discord and Telegram bots
echo "Starting Discord bot..."
poetry run python3 /app/src/main.py &

echo "Starting Telegram bot..."
poetry run python3 /app/src/telegram_bot/main.py &

# Wait for both processes
wait
