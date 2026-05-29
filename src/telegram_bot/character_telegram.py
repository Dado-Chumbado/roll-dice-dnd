"""Telegram handlers for character sheet commands."""

import logging
import html as _html

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from plugins.character.character_manager import (
    load_character, list_characters,
    update_hp, use_slot, reset_slot, rest, update_inventory,
    update_currency, set_ca, add_weapon, remove_weapon,
    COIN_LABELS, resolve_coin,
)
from telegram_bot.sheet_formatter_telegram import (
    format_sheet_simple_telegram,
    format_sheet_full_telegram,
)
from telegram_bot.bot import is_chat_allowed

logger = logging.getLogger(__name__)


def _player_name(update: Update, args: list, index: int = 0) -> str:
    """Return args[index] if present, else Telegram username/first_name."""
    if len(args) > index:
        return args[index].lower()
    user = update.effective_user
    return (user.username or user.first_name or f"user{user.id}").lower()


def _hp_bar(current: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        return ""
    filled = round(max(0, min(current / maximum, 1)) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _sign(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


async def _send_html(update: Update, text: str) -> None:
    if len(text) <= 4096:
        await update.message.reply_text(text, parse_mode="HTML")
        return
    chunk, lines = "", text.split("\n")
    for line in lines:
        if len(chunk) + len(line) + 1 > 4096:
            await update.message.reply_text(chunk, parse_mode="HTML")
            chunk = line
        else:
            chunk = chunk + "\n" + line if chunk else line
    if chunk:
        await update.message.reply_text(chunk, parse_mode="HTML")


# ---------------------------------------------------------------------------
# /ficha [completa] [nome]
# ---------------------------------------------------------------------------

async def ficha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []

    if args and args[0].lower() == "completa":
        mode = "completa"
        name = _player_name(update, args, index=1)
    else:
        mode = "simples"
        name = _player_name(update, args, index=0)

    data = load_character(name)
    if data is None:
        available = list_characters()
        hint = f" Fichas: {', '.join(available)}" if available else ""
        await update.message.reply_text(
            f"Ficha de '{_html.escape(name)}' não encontrada.{hint}\n"
            f"Use /importar para importar o PDF.",
            parse_mode="HTML",
        )
        return

    text = format_sheet_full_telegram(data) if mode == "completa" else format_sheet_simple_telegram(data)
    await _send_html(update, text)


# ---------------------------------------------------------------------------
# /hp <delta> [nome]    ex: /hp -8   /hp +4   /hp 10
# ---------------------------------------------------------------------------

async def hp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []

    if not args:
        await update.message.reply_text("Uso: /hp -8 ou /hp +4 [nome]")
        return
    try:
        delta = int(args[0])
    except ValueError:
        await update.message.reply_text("Uso: /hp -8 ou /hp +4 [nome]")
        return

    name = _player_name(update, args, index=1)
    try:
        data = update_hp(name, delta)
    except FileNotFoundError as e:
        await update.message.reply_text(str(e))
        return

    hp_cur = data["session"]["hp_current"]
    hp_max = data["base"]["hp_max"]
    char   = data["base"]["name"]
    bar    = _hp_bar(hp_cur, hp_max)
    verb   = "recuperou" if delta >= 0 else "sofreu"
    emoji  = "❤️" if delta >= 0 else "🩸"
    await _send_html(
        update,
        f"{emoji} <b>{_html.escape(char)}</b> {verb} <b>{abs(delta)} HP</b> — "
        f"HP: <b>{hp_cur}/{hp_max}</b> {bar}",
    )


# ---------------------------------------------------------------------------
# /slot <nivel> [reset] [nome]
# ---------------------------------------------------------------------------

async def slot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []

    if not args:
        await update.message.reply_text("Uso: /slot <nivel> [reset] [nome]")
        return

    level = args[0]
    is_reset = len(args) > 1 and args[1].lower() == "reset"
    name = _player_name(update, args, index=2 if is_reset else 1)

    try:
        data = reset_slot(name, level) if is_reset else use_slot(name, level)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return

    slots_max  = data["base"]["spell_slots_max"]
    slots_used = data["session"]["spell_slots_used"]
    used  = slots_used.get(level, 0)
    total = slots_max.get(level, 0)
    pips  = "◆" * (total - used) + "◇" * used
    verb  = "restaurados" if is_reset else "usado"
    await _send_html(
        update,
        f"✨ Slot nível <b>{level}</b> {verb} — {pips} ({total - used}/{total})",
    )


# ---------------------------------------------------------------------------
# /slots [nome]
# ---------------------------------------------------------------------------

async def slots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    name = _player_name(update, context.args or [])
    data = load_character(name)
    if data is None:
        await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
        return

    slots_max  = data["base"].get("spell_slots_max", {})
    slots_used = data["session"].get("spell_slots_used", {})
    char = data["base"]["name"]

    if not slots_max:
        await update.message.reply_text(f"<b>{_html.escape(char)}</b> não possui slots de magia.", parse_mode="HTML")
        return

    lines = [f"✨ <b>Slots — {_html.escape(char)}</b>"]
    for lvl in sorted(slots_max.keys(), key=int):
        total     = slots_max[lvl]
        remaining = total - slots_used.get(lvl, 0)
        pips      = "◆" * remaining + "◇" * (total - remaining)
        lines.append(f"  Nível {lvl}: {pips} ({remaining}/{total})")
    await _send_html(update, "\n".join(lines))


# ---------------------------------------------------------------------------
# /descanso <curto|longo> [nome]
# ---------------------------------------------------------------------------

async def descanso_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []

    if not args or args[0].lower() not in ("curto", "longo"):
        await update.message.reply_text("Uso: /descanso curto  ou  /descanso longo [nome]")
        return

    tipo = args[0].lower()
    name = _player_name(update, args, index=1)

    try:
        data = rest(name, tipo)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return

    char   = data["base"]["name"]
    hp_cur = data["session"]["hp_current"]
    hp_max = data["base"]["hp_max"]
    bar    = _hp_bar(hp_cur, hp_max)
    emoji  = "🌙" if tipo == "longo" else "💤"
    await _send_html(
        update,
        f"{emoji} <b>{_html.escape(char)}</b> descansou ({tipo})! "
        f"HP: <b>{hp_cur}/{hp_max}</b> {bar}",
    )


# ---------------------------------------------------------------------------
# /inventario [nome]
# ---------------------------------------------------------------------------

async def inventario_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    name = _player_name(update, context.args or [])
    data = load_character(name)
    if data is None:
        await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
        return

    char      = data["base"]["name"]
    inventory = data["session"]["inventory"]
    currency  = data["session"].get("currency", {})

    if not inventory:
        await update.message.reply_text(
            f"🎒 <b>{_html.escape(char)}</b> não possui itens.", parse_mode="HTML"
        )
        return

    lines = [f"🎒 <b>Inventário — {_html.escape(char)}</b>"]
    for item in inventory:
        qty    = item.get("qty", 1)
        weight = item.get("weight")
        w_str  = f" ({weight})" if weight and weight != "--" else ""
        lines.append(f"  • {_html.escape(item['name'])} x{qty}{_html.escape(w_str)}")

    coins = [
        f"{v} {lbl}" for k, lbl in [("pp","PPl"),("gp","PO"),("ep","PE"),("sp","PP"),("cp","PC")]
        if (v := currency.get(k, 0))
    ]
    if coins:
        lines.append(f"\n💰 <b>Moedas:</b> {' | '.join(coins)}")

    await _send_html(update, "\n".join(lines))


# ---------------------------------------------------------------------------
# /item_add <nome> [qty] [nome_jogador]
# /item_rem <nome> [qty] [nome_jogador]
# ---------------------------------------------------------------------------

async def _item_handler(update: Update, args: list, add: bool) -> None:
    if not args:
        cmd = "item_add" if add else "item_rem"
        await update.message.reply_text(f"Uso: /{cmd} <item> [qty]")
        return

    # Last arg is qty if it's a digit, second-to-last if we also have a player name
    # Simple approach: trailing integer = qty, rest = item name
    if len(args) >= 2 and args[-1].isdigit():
        qty       = int(args[-1])
        item_name = " ".join(args[:-1])
    else:
        qty       = 1
        item_name = " ".join(args)

    name = _player_name(update, [], index=0)  # always default to telegram user

    try:
        data = update_inventory(name, item_name, qty, add=add)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return

    char  = data["base"]["name"]
    emoji = "➕" if add else "➖"
    verb  = "adicionado" if add else "removido"
    await update.message.reply_text(
        f"{emoji} <b>{_html.escape(char)}</b>: {_html.escape(item_name)} x{qty} {verb}.",
        parse_mode="HTML",
    )


async def item_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    await _item_handler(update, context.args or [], add=True)


async def item_rem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    await _item_handler(update, context.args or [], add=False)


# ---------------------------------------------------------------------------
# /moeda <+/-delta> <tipo> [nome]   ex: /moeda +10 po   /moeda -3 pp trovao
# ---------------------------------------------------------------------------

async def moeda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Uso: /moeda +10 po [nome]  (tipos: pc, pp, pe, po, ppl)")
        return
    try:
        delta = int(args[0])
    except ValueError:
        await update.message.reply_text("Uso: /moeda +10 po [nome]  (tipos: pc, pp, pe, po, ppl)")
        return
    try:
        key = resolve_coin(args[1])
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    name = _player_name(update, args, index=2)
    try:
        data = update_currency(name, args[1], delta)
    except FileNotFoundError as e:
        await update.message.reply_text(str(e))
        return

    char     = data["base"]["name"]
    currency = data["session"].get("currency", {})
    new_val  = currency.get(key, 0)
    label    = COIN_LABELS.get(key, args[1].upper())
    verb     = "recebeu" if delta >= 0 else "gastou"
    await _send_html(
        update,
        f"💰 <b>{_html.escape(char)}</b> {verb} <b>{abs(delta)} {label}</b> — "
        f"saldo: <b>{new_val} {label}</b>",
    )


# ---------------------------------------------------------------------------
# /ca <valor> [nome]
# ---------------------------------------------------------------------------

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /ca <valor> [nome]")
        return
    try:
        value = int(args[0])
    except ValueError:
        await update.message.reply_text("Uso: /ca <valor> [nome]")
        return
    name = _player_name(update, args, index=1)
    try:
        data = set_ca(name, value)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return
    char = data["base"]["name"]
    await _send_html(update, f"🛡️ <b>{_html.escape(char)}</b> — CA atualizada para <b>{value}</b>")


# ---------------------------------------------------------------------------
# /arma_add <nome> [atk] [dano] [notas]
# /arma_rem <nome>
# /arma_list [nome]
# ---------------------------------------------------------------------------

async def arma_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re as _re
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /arma_add <nome> [atk] [dano] [notas]")
        return

    name = _player_name(update, [], index=0)

    dice_re = _re.compile(r'^\d*d\d+', _re.IGNORECASE)
    atk_re  = _re.compile(r'^[+-]\d+$')

    remaining = list(args)
    notes = ""
    atk_bonus = ""
    damage = ""

    if len(remaining) >= 2 and not dice_re.match(remaining[-1]) and not atk_re.match(remaining[-1]):
        notes = remaining[-1]
        remaining = remaining[:-1]

    if remaining and dice_re.match(remaining[-1]):
        damage = remaining[-1]
        remaining = remaining[:-1]

    if remaining and atk_re.match(remaining[-1]):
        atk_bonus = remaining[-1]
        remaining = remaining[:-1]

    weapon_name = " ".join(remaining).strip()
    if not weapon_name:
        await update.message.reply_text("Informe o nome da arma.")
        return

    try:
        data = add_weapon(name, weapon_name, atk_bonus, damage, notes)
    except FileNotFoundError as e:
        await update.message.reply_text(str(e))
        return

    char  = data["base"]["name"]
    parts = [f"<b>{_html.escape(weapon_name)}</b>"]
    if atk_bonus:
        parts.append(f"Atk: {atk_bonus}")
    if damage:
        parts.append(f"Dano: {damage}")
    if notes:
        parts.append(_html.escape(notes))
    await _send_html(update, f"➕ <b>{_html.escape(char)}</b>: {' | '.join(parts)} adicionada.")


async def arma_rem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /arma_rem <nome_arma>")
        return
    name        = _player_name(update, [], index=0)
    weapon_name = " ".join(args).strip()
    try:
        data = remove_weapon(name, weapon_name)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return
    char = data["base"]["name"]
    await _send_html(update, f"➖ <b>{_html.escape(char)}</b>: arma <b>{_html.escape(weapon_name)}</b> removida.")


async def arma_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    name = _player_name(update, context.args or [])
    data = load_character(name)
    if data is None:
        await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
        return
    attacks = data["base"].get("attacks", [])
    char    = data["base"]["name"]
    if not attacks:
        await update.message.reply_text(f"<b>{_html.escape(char)}</b> não possui armas cadastradas.", parse_mode="HTML")
        return
    lines = [f"⚔️ <b>Armas — {_html.escape(char)}</b>"]
    for w in attacks:
        atk   = f" | Atk: {w['atk_bonus']}" if w.get("atk_bonus") else ""
        dmg   = f" | Dano: {w['damage']}" if w.get("damage") else ""
        notes = f" | {_html.escape(w['notes'])}" if w.get("notes") else ""
        lines.append(f"  • <b>{_html.escape(w['name'])}</b>{atk}{dmg}{notes}")
    await _send_html(update, "\n".join(lines))


# ---------------------------------------------------------------------------
# Register all handlers
# ---------------------------------------------------------------------------

def register_character_handlers(app) -> None:
    app.add_handler(CommandHandler("ficha",      ficha_command))
    app.add_handler(CommandHandler("hp",         hp_command))
    app.add_handler(CommandHandler("slot",       slot_command))
    app.add_handler(CommandHandler("slots",      slots_command))
    app.add_handler(CommandHandler("descanso",   descanso_command))
    app.add_handler(CommandHandler("inventario", inventario_command))
    app.add_handler(CommandHandler("item_add",   item_add_command))
    app.add_handler(CommandHandler("item_rem",   item_rem_command))
    app.add_handler(CommandHandler("moeda",      moeda_command))
    app.add_handler(CommandHandler("ca",         ca_command))
    app.add_handler(CommandHandler("arma_add",   arma_add_command))
    app.add_handler(CommandHandler("arma_rem",   arma_rem_command))
    app.add_handler(CommandHandler("arma_list",  arma_list_command))
    logger.info("Character sheet handlers registered.")
