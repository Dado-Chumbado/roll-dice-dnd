"""Core logic for the Telegram dice bot."""

import io
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from core.dice_engine import process_input_dice
from telegram_bot.roll_view_telegram import get_roll_text_telegram
from telegram_bot.d20_irl_client import D20IRLClient, D20IRLError, add_gif_loop_pause

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
    allowed = chat_id in allowed_list
    if not allowed:
        logger.warning(f"Blocked chat_id={chat_id} (not in whitelist: {allowed_list})")
    return allowed


def _log_command(update: Update, command: str, args: list = None):
    user = update.effective_user
    chat = update.effective_chat
    logger.info(
        f"Command /{command} | user={user.username or user.first_name}({user.id}) "
        f"chat={chat.title or chat.username or chat.id}({chat.id}) args={args or []}"
    )


async def _handle_roll(update: Update, context: ContextTypes.DEFAULT_TYPE, adv: bool = None):
    """Shared handler for roll commands."""
    if not is_chat_allowed(update):
        await update.message.reply_text("This bot is not authorized for this chat.")
        return

    dice_expr = " ".join(context.args) if context.args else "d20"
    ctx = TelegramContext(update)
    logger.info(f"Rolling expr='{dice_expr}' adv={adv} user={ctx.author.nick}")

    try:
        dice_roll_list, dice_data, reroll = await process_input_dice(ctx, dice_expr, adv=adv)

        for roll in dice_roll_list:
            text = await get_roll_text_telegram(ctx, roll, dice_data, reroll)

            if len(text) <= 4096:
                await update.message.reply_text(text, parse_mode="HTML")
            else:
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
                    await update.message.reply_text(chunk, parse_mode="HTML")

        logger.info(f"Roll OK expr='{dice_expr}' user={ctx.author.nick}")

    except Exception as e:
        logger.error(f"Roll failed expr='{dice_expr}' user={ctx.author.nick}: {e}", exc_info=True)
        await update.message.reply_text(f"Error processing roll: {str(e)}")


async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /roll and /r commands."""
    _log_command(update, "roll", context.args)
    await _handle_roll(update, context, adv=None)


async def advantage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adv and /v commands for advantage rolls."""
    _log_command(update, "adv", context.args)
    await _handle_roll(update, context, adv=True)


async def disadvantage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /dis and /d commands for disadvantage rolls."""
    _log_command(update, "dis", context.args)
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
    irl_enabled = os.getenv("D20_IRL_ENABLED", "").strip().lower() in ("1", "true", "yes")
    irl_command_name = os.getenv("D20_IRL_COMMAND", "irl").strip() or "irl"
    irl_section = f"""
**Physical D20 (IRL):**
• `/{irl_command_name}` - Roll a real physical D20
• `/{irl_command_name} adv` - Roll with advantage (picks highest)
• `/{irl_command_name} dis` - Roll with disadvantage (picks lowest)
""" if irl_enabled else ""

    help_text = f"""🎲 **D&D Dice Roller Bot**

**Rolagem de Dados:**
• `/roll <expr>` ou `/r <expr>` — Rolar dados
  Exemplos: `/r 2d6+3`, `/r d20`, `/r 1d8+1d6`
• `/adv <expr>` — Rolar com vantagem (2d20, maior)
• `/dis <expr>` — Rolar com desvantagem (2d20, menor)
{irl_section}
**Ficha de Personagem:**
• `/ficha [nome]` — Resumo da ficha (HP, CA, atributos, ataques)
• `/ficha completa [nome]` — Ficha completa
• `/hp -8` ou `/hp +4 [nome]` — Dano ou cura
• `/slot <nivel> [reset] [nome]` — Usa ou restaura slot de magia
• `/slots [nome]` — Mostra slots disponíveis
• `/descanso <curto|longo> [nome]` — Descansa
• `/inventario [nome]` — Mostra inventário
• `/item_add <item> [qty]` — Adiciona item ao inventário
• `/item_rem <item> [qty]` — Remove item do inventário
• `/moeda +10 po [nome]` — Atualiza moedas (pc, pp, pe, po, ppl)
• `/ca <valor> [nome]` — Define CA manualmente
• `/arma_add <nome> [atk] [dano] [notas]` — Adiciona arma
• `/arma_rem <nome>` — Remove arma
• `/arma_list [nome]` — Lista armas

> Para importar uma ficha, use `!importar` no Discord com o PDF em anexo.

**Expressões de Dados:**
• `d20` — Um d20 (padrão)
• `2d6` — 2 dados de 6
• `1d8+3` — d8 mais 3
• `2d6+1d4` — Múltiplos tipos

**Outros:**
• `/help` — Esta ajuda
• `/chatid` — ID do chat para whitelist
"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def irl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the IRL physical dice roll command."""
    _log_command(update, "irl", context.args)

    if not is_chat_allowed(update):
        await update.message.reply_text("This bot is not authorized for this chat.")
        return

    base_url = os.getenv("D20_IRL_URL", "").strip()
    if not base_url:
        logger.error("IRL: D20_IRL_URL is not set")
        await update.message.reply_text(
            "D20 IRL is not configured. Set D20_IRL_URL in your environment."
        )
        return

    arg = (context.args[0].lower() if context.args else "").strip()
    mode_map = {"adv": "advantage", "advantage": "advantage",
                "dis": "disadvantage", "disadvantage": "disadvantage"}
    mode = mode_map.get(arg, "normal")

    username = os.getenv("D20_IRL_USERNAME", "").strip()
    token = os.getenv("D20_IRL_TOKEN", "").strip()

    if not username or not token:
        logger.error(f"IRL: auth not configured (username={'set' if username else 'MISSING'}, token={'set' if token else 'MISSING'})")
        await update.message.reply_text(
            "D20 IRL auth is not configured. Set D20_IRL_USERNAME and D20_IRL_TOKEN in your environment."
        )
        return

    logger.info(f"IRL: starting roll mode={mode} url={base_url} username={username}")
    status_msg = await update.message.reply_text("Rolling your physical D20...")

    try:
        client = D20IRLClient(base_url, username=username, token=token)

        result = None
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            logger.info(f"IRL: roll attempt {attempt}/{max_attempts}")
            result = await client.roll(mode=mode)
            logger.info(f"IRL: attempt {attempt} result face={result['face']} detections={result['detections']}")
            if result["face"] is not None:
                break
            if attempt < max_attempts:
                logger.warning(f"IRL: attempt {attempt} returned no detection, retrying...")
                await status_msg.edit_text(f"Dice not detected, retrying... ({attempt}/{max_attempts})")

        if result is None or result["face"] is None:
            logger.error("IRL: all attempts failed, no detection")
            await status_msg.edit_text("Could not detect the dice after 3 attempts. Please try again.")
            return

        face = result["face"]
        detections = result["detections"]
        logger.info(f"IRL: roll success face={face} mode={mode} gif_url={result['gif_url']} image_url={result['image_url']}")

        if mode != "normal" and len(detections) > 1:
            dice_str = ", ".join(f"{d['face']}" for d in detections)
            caption = (
                f"Rolled: <b>{face}</b>  [{mode}]\n"
                f"<i>Detected: {dice_str}</i>"
            )
        else:
            caption = f"Rolled: <b>{face}</b>"

        if result["gif_url"]:
            try:
                logger.info(f"IRL: fetching GIF from {result['gif_url']}")
                gif_bytes = await client.fetch_bytes(result["gif_url"])
                gif_bytes = add_gif_loop_pause(gif_bytes, pause_ms=3000)
                gif_bio = io.BytesIO(gif_bytes)
                gif_bio.name = "roll.gif"
                await update.message.reply_animation(gif_bio)
                logger.info("IRL: GIF sent")
            except Exception as e:
                logger.warning(f"IRL: failed to send GIF: {e}", exc_info=True)

        if result["image_url"]:
            try:
                logger.info(f"IRL: fetching image from {result['image_url']}")
                image_bytes = await client.fetch_bytes(result["image_url"])
                img_bio = io.BytesIO(image_bytes)
                img_bio.name = "roll.jpg"
                await update.message.reply_photo(img_bio, caption=caption, parse_mode="HTML")
                logger.info("IRL: image sent")
            except Exception as e:
                logger.warning(f"IRL: failed to send image: {e}", exc_info=True)
                await update.message.reply_text(caption, parse_mode="HTML")
        else:
            logger.warning("IRL: no image_url in result, sending text only")
            await update.message.reply_text(caption, parse_mode="HTML")

        await status_msg.delete()
        logger.info("IRL: command completed successfully")

    except D20IRLError as e:
        logger.error(f"IRL: D20IRLError: {e}")
        await status_msg.edit_text(f"IRL roll failed: {e}")
    except Exception as e:
        logger.error(f"IRL: unexpected error: {e}", exc_info=True)
        await status_msg.edit_text("IRL roll failed. Is the Raspberry Pi reachable?")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - welcome message."""
    welcome_text = """🎲 Welcome to the D&D Dice Roller Bot!

I can help you roll dice for your tabletop RPG sessions.

Use `/help` to see all available commands.

Quick start: Just type `/r 2d6` to roll 2 six-sided dice!
"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


def _get_cmd(env_var: str, default: str) -> list[str]:
    """Read a command name from env, falling back to default. Supports comma-separated aliases."""
    val = os.getenv(env_var, "").strip()
    names = [v.strip() for v in val.split(",") if v.strip()] if val else []
    return names if names else [default]


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception in Telegram handler", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Ocorreu um erro interno. Tente novamente.")


def create_telegram_bot(token: str) -> Application:
    """Create and configure the Telegram bot application."""
    from telegram_bot.character_telegram import register_character_handlers
    app = Application.builder().token(token).build()
    app.add_error_handler(_error_handler)

    roll_cmd = _get_cmd("TELEGRAM_CMD_ROLL", "roll") + ["r"]
    adv_cmd  = _get_cmd("TELEGRAM_CMD_ADV", "adv")
    dis_cmd  = _get_cmd("TELEGRAM_CMD_DIS", "dis")

    logger.info(f"Commands: roll={roll_cmd} adv={adv_cmd} dis={dis_cmd}")

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler(roll_cmd, roll_command))
    app.add_handler(CommandHandler(adv_cmd, advantage_command))
    app.add_handler(CommandHandler(dis_cmd, disadvantage_command))
    app.add_handler(CommandHandler("chatid", chatid_command))

    register_character_handlers(app)

    # IRL integration is opt-in via D20_IRL_ENABLED=true
    if os.getenv("D20_IRL_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        irl_command_name = os.getenv("D20_IRL_COMMAND", "irl").strip() or "irl"
        app.add_handler(CommandHandler(irl_command_name, irl_command))
        logger.info(f"D20 IRL integration enabled (/{irl_command_name})")

    return app
