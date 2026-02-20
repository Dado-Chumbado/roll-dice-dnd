"""Core logic for the Telegram dice bot."""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from core.dice_engine import process_input_dice
from core.roll_view import get_roll_text

logger = logging.getLogger(__name__)


class TelegramContext:
    """Adapter to make Telegram Update compatible with core dice engine expectations."""

    class Author:
        def __init__(self, user_id, nickname):
            self.id = user_id
            self.nick = nickname

    class Channel:
        def __init__(self, name):
            self.name = name

    def __init__(self, update: Update):
        self._update = update
        user = update.effective_user
        chat = update.effective_chat

        self.author = self.Author(
            user_id=user.id,
            nickname=user.username or user.first_name or f"User{user.id}"
        )
        self.channel = self.Channel(
            name=chat.title or chat.username or f"Chat{chat.id}"
        )

    async def send(self, message: str):
        """Send a message back to the chat."""
        await self._update.message.reply_text(message)


def is_chat_allowed(update: Update) -> bool:
    """Check if the chat is in the whitelist. Empty whitelist = allow all."""
    allowed_chats = os.getenv("telegram_allowed_chats", "").strip()

    if not allowed_chats:
        return True  # Empty = allow all

    chat_id = str(update.effective_chat.id)
    allowed_list = [c.strip() for c in allowed_chats.split(",")]
    return chat_id in allowed_list


def adapt_for_telegram(text: str) -> str:
    """Adapt Discord-formatted output for Telegram."""
    # Replace sparkles emoji shortcode with unicode
    text = text.replace(":sparkles:", "✨")

    # Remove blockquote markers (Telegram uses different markdown)
    text = text.replace(">>> ", "")

    return text


async def _handle_roll(update: Update, context: ContextTypes.DEFAULT_TYPE, adv: bool = None):
    """Shared handler for roll commands."""
    if not is_chat_allowed(update):
        await update.message.reply_text("This bot is not authorized for this chat.")
        return

    # Get dice expression from command args, default to "d20"
    dice_expr = " ".join(context.args) if context.args else "d20"

    # Create adapter context
    ctx = TelegramContext(update)

    try:
        # Process dice roll using core engine
        dice_roll_list, dice_data, reroll = await process_input_dice(ctx, dice_expr, adv=adv)

        # Format output for each roll
        for roll in dice_roll_list:
            text = await get_roll_text(ctx, roll, dice_data, reroll)
            text = adapt_for_telegram(text)

            # Split message if it exceeds Telegram's 4096 character limit
            if len(text) <= 4096:
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                # Split into chunks at line boundaries
                chunks = []
                current_chunk = ""
                for line in text.split("\n"):
                    if len(current_chunk) + len(line) + 1 > 4096:
                        chunks.append(current_chunk)
                        current_chunk = line
                    else:
                        current_chunk += "\n" + line if current_chunk else line

                if current_chunk:
                    chunks.append(current_chunk)

                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error processing roll: {e}", exc_info=True)
        await update.message.reply_text(f"Error processing roll: {str(e)}")


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /roll and /r commands."""
    await _handle_roll(update, context, adv=None)


async def advantage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adv and /v commands for advantage rolls."""
    await _handle_roll(update, context, adv=True)


async def disadvantage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dis and /d commands for disadvantage rolls."""
    await _handle_roll(update, context, adv=False)


async def chatid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /chatid command - returns the current chat ID."""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_name = update.effective_chat.title or update.effective_chat.username or "Private Chat"

    message = f"📋 **Chat Information**\n\n"
    message += f"**Chat ID:** `{chat_id}`\n"
    message += f"**Chat Type:** {chat_type}\n"
    message += f"**Chat Name:** {chat_name}\n\n"
    message += f"To whitelist this chat, add this ID to your `.env` file:\n"
    message += f"`telegram_allowed_chats={chat_id}`"

    await update.message.reply_text(message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - shows available commands."""
    help_text = """🎲 **D&D Dice Roller Bot**

**Rolling Dice:**
• `/roll <expr>` or `/r <expr>` - Roll dice
  Examples: `/r 2d6+3`, `/r d20`, `/r 1d8+1d6`

• `/adv <expr>` or `/v <expr>` - Roll with advantage
  Example: `/adv` (rolls 2d20, takes highest)

• `/dis <expr>` or `/d <expr>` - Roll with disadvantage
  Example: `/dis` (rolls 2d20, takes lowest)

**Dice Expressions:**
• `d20` - Single d20 (default if no expression given)
• `2d6` - Roll 2 six-sided dice
• `1d8+3` - Roll d8 and add 3
• `2d6+1d4` - Multiple dice types
• `3d8-2` - Roll and subtract

**Other Commands:**
• `/help` - Show this help message
• `/chatid` - Get chat ID for whitelisting

**Examples:**
`/r 2d6+3` → Roll 2d6 and add 3
`/adv` → Roll d20 with advantage
`/dis 1d20+5` → Roll d20 with disadvantage, add 5
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - welcome message."""
    welcome_text = """🎲 Welcome to the D&D Dice Roller Bot!

I can help you roll dice for your tabletop RPG sessions.

Use `/help` to see all available commands.

Quick start: Just type `/r 2d6` to roll 2 six-sided dice!
"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


def create_telegram_bot(token: str) -> Application:
    """Create and configure the Telegram bot application."""
    app = Application.builder().token(token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler(["roll", "r"], roll_command))
    app.add_handler(CommandHandler(["adv", "v"], advantage_command))
    app.add_handler(CommandHandler(["dis", "d"], disadvantage_command))
    app.add_handler(CommandHandler("chatid", chatid_command))

    return app
