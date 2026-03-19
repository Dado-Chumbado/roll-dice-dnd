#!/bin/bash
set -e

# Forward SIGTERM/SIGINT to child processes so they shut down cleanly
# before Docker kills the container. Without this, the Telegram bot may
# not release its getUpdates session, causing HTTP 409 on the next start.
cleanup() {
    echo "Shutting down bots..."
    kill "$DISCORD_PID" "$TELEGRAM_PID" 2>/dev/null
    wait "$DISCORD_PID" "$TELEGRAM_PID" 2>/dev/null
    echo "Bots stopped."
}
trap cleanup SIGTERM SIGINT

echo "Starting Discord bot..."
poetry run python3 /app/src/main.py &
DISCORD_PID=$!

echo "Starting Telegram bot..."
poetry run python3 /app/src/telegram_bot/main.py &
TELEGRAM_PID=$!

echo "Both bots started (Discord PID: $DISCORD_PID, Telegram PID: $TELEGRAM_PID)"

# Wait for both processes
wait "$DISCORD_PID" "$TELEGRAM_PID"
