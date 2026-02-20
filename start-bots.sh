#!/bin/bash
set -e

echo "Starting Discord bot..."
poetry run python3 /app/src/main.py &
DISCORD_PID=$!

echo "Starting Telegram bot..."
poetry run python3 /app/src/telegram_bot/main.py &
TELEGRAM_PID=$!

echo "Both bots started (Discord PID: $DISCORD_PID, Telegram PID: $TELEGRAM_PID)"

# Wait for both processes
wait
