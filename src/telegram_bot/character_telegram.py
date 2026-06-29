"""Telegram handlers for character sheet commands."""

import re
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
    format_spells_telegram,
    format_spell_detail_telegram,
)
from telegram_bot.bot import is_chat_allowed

logger = logging.getLogger(__name__)

_DICE_RE  = re.compile(r'^\d*d\d+', re.IGNORECASE)
_ATK_RE   = re.compile(r'^[+-]?\d+$')
_NUM_RE   = re.compile(r'^[+-]?\d+$')


def _default_name(update: Update) -> str:
    user = update.effective_user
    return (user.username or user.first_name or f"user{user.id}").lower()


def _resolve(update: Update, args: list, index: int = 0) -> str:
    """Return args[index].lower() if present, else Telegram username."""
    if len(args) > index:
        return args[index].lower()
    return _default_name(update)


def _is_number(s: str) -> bool:
    return bool(_NUM_RE.match(s))


def _split_name(update: Update, args: list) -> tuple[str, list]:
    """If first arg is NOT a number/keyword, treat it as char name.
    Returns (name, remaining_args).
    """
    if args and not _is_number(args[0]):
        return args[0].lower(), args[1:]
    return _default_name(update), args


def _hp_bar(current: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        return ""
    filled = round(max(0, min(current / maximum, 1)) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


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
# /ficha [nome] [completa]
# ---------------------------------------------------------------------------

async def ficha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []

    # Detect "completa" keyword anywhere in args
    mode = "simples"
    filtered = []
    for a in args:
        if a.lower() == "completa":
            mode = "completa"
        else:
            filtered.append(a)

    name = _resolve(update, filtered, index=0)
    data = load_character(name)
    if data is None:
        available = list_characters()
        hint = f" Fichas: {', '.join(available)}" if available else ""
        await update.message.reply_text(
            f"Ficha de '{_html.escape(name)}' não encontrada.{hint}",
            parse_mode="HTML",
        )
        return

    text = format_sheet_full_telegram(data) if mode == "completa" else format_sheet_simple_telegram(data)
    await _send_html(update, text)


# ---------------------------------------------------------------------------
# /hp [nome] <delta>     ex: /hp -8   /hp trovao +4
# ---------------------------------------------------------------------------

async def hp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /hp [nome] -8  ou  /hp [nome] +4")
        return

    name, rest_args = _split_name(update, args)
    if not rest_args:
        await update.message.reply_text("Uso: /hp [nome] -8  ou  /hp [nome] +4")
        return
    try:
        delta = int(rest_args[0])
    except ValueError:
        await update.message.reply_text("Uso: /hp [nome] -8  ou  /hp [nome] +4")
        return

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
# /slot [nome] <nivel> [reset]
# ---------------------------------------------------------------------------

async def slot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /slot [nome] <nivel> [reset]")
        return

    name, rest_args = _split_name(update, args)
    if not rest_args:
        await update.message.reply_text("Uso: /slot [nome] <nivel> [reset]")
        return

    level    = rest_args[0]
    is_reset = len(rest_args) > 1 and rest_args[1].lower() == "reset"

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
    name = _resolve(update, context.args or [])
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
# /descanso [nome] <curto|longo>
# ---------------------------------------------------------------------------

async def descanso_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /descanso [nome] curto  ou  /descanso [nome] longo")
        return

    # Detect tipo keyword
    tipo = None
    filtered = []
    for a in args:
        if a.lower() in ("curto", "longo"):
            tipo = a.lower()
        else:
            filtered.append(a)

    if not tipo:
        await update.message.reply_text("Uso: /descanso [nome] curto  ou  /descanso [nome] longo")
        return

    name = _resolve(update, filtered, index=0)
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
    name = _resolve(update, context.args or [])
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
# /item adicionar <nome> <item> [qty]
# /item remover <nome> <item> [qty]
# ---------------------------------------------------------------------------

async def item_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if len(args) < 3 or args[0].lower() not in ("adicionar", "remover"):
        await update.message.reply_text(
            "Uso:\n"
            "/item adicionar <nome> <item> [qty]\n"
            "/item remover <nome> <item> [qty]"
        )
        return

    action = args[0].lower()
    name   = args[1].lower()
    rest_args = args[2:]

    if len(rest_args) >= 2 and rest_args[-1].isdigit():
        qty       = int(rest_args[-1])
        item_name = " ".join(rest_args[:-1])
    else:
        qty       = 1
        item_name = " ".join(rest_args)

    if not item_name:
        await update.message.reply_text("Informe o nome do item.")
        return

    try:
        data = update_inventory(name, item_name, qty, add=(action == "adicionar"))
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return

    char  = data["base"]["name"]
    emoji = "➕" if action == "adicionar" else "➖"
    verb  = "adicionado" if action == "adicionar" else "removido"
    await _send_html(
        update,
        f"{emoji} <b>{_html.escape(char)}</b>: {_html.escape(item_name)} x{qty} {verb}.",
    )


# ---------------------------------------------------------------------------
# /moeda [nome] <+/-delta> <tipo>   ex: /moeda trovao +10 po
# ---------------------------------------------------------------------------

async def moeda_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Uso: /moeda [nome] +10 po  (tipos: pc, pp, pe, po, ppl)")
        return

    name, rest_args = _split_name(update, args)
    if len(rest_args) < 2:
        await update.message.reply_text("Uso: /moeda [nome] +10 po  (tipos: pc, pp, pe, po, ppl)")
        return

    try:
        delta = int(rest_args[0])
    except ValueError:
        await update.message.reply_text("Uso: /moeda [nome] +10 po  (tipos: pc, pp, pe, po, ppl)")
        return
    try:
        key = resolve_coin(rest_args[1])
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    try:
        data = update_currency(name, rest_args[1], delta)
    except FileNotFoundError as e:
        await update.message.reply_text(str(e))
        return

    char    = data["base"]["name"]
    new_val = data["session"].get("currency", {}).get(key, 0)
    label   = COIN_LABELS.get(key, rest_args[1].upper())
    verb    = "recebeu" if delta >= 0 else "gastou"
    await _send_html(
        update,
        f"💰 <b>{_html.escape(char)}</b> {verb} <b>{abs(delta)} {label}</b> — "
        f"saldo: <b>{new_val} {label}</b>",
    )


# ---------------------------------------------------------------------------
# /ca [nome] <valor>
# ---------------------------------------------------------------------------

async def ca_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /ca [nome] <valor>")
        return

    name, rest_args = _split_name(update, args)
    if not rest_args:
        await update.message.reply_text("Uso: /ca [nome] <valor>")
        return
    try:
        value = int(rest_args[0])
    except ValueError:
        await update.message.reply_text("Uso: /ca [nome] <valor>")
        return

    try:
        data = set_ca(name, value)
    except (FileNotFoundError, ValueError) as e:
        await update.message.reply_text(str(e))
        return

    char = data["base"]["name"]
    await _send_html(update, f"🛡️ <b>{_html.escape(char)}</b> — CA atualizada para <b>{value}</b>")


# ---------------------------------------------------------------------------
# /arma adicionar <nome> <arma> [atk] [dano] [notas]
# /arma remover <nome> <arma>
# /arma listar [nome]
# ---------------------------------------------------------------------------

async def arma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args or args[0].lower() not in ("adicionar", "remover", "listar"):
        await update.message.reply_text(
            "Uso:\n"
            "/arma adicionar <nome> <arma> [atk] [dano] [notas]\n"
            "/arma remover <nome> <arma>\n"
            "/arma listar [nome]"
        )
        return

    action = args[0].lower()

    if action == "listar":
        name = _resolve(update, args, index=1)
        data = load_character(name)
        if data is None:
            await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
            return
        attacks = data["base"].get("attacks", [])
        char    = data["base"]["name"]
        if not attacks:
            await update.message.reply_text(f"<b>{_html.escape(char)}</b> não possui armas.", parse_mode="HTML")
            return
        lines = [f"⚔️ <b>Armas — {_html.escape(char)}</b>"]
        for w in attacks:
            atk   = f" | Atk: {w['bonus']}" if w.get("bonus") else ""
            dmg   = f" | Dano: {w['damage']}" if w.get("damage") else ""
            notes = f" | {_html.escape(w['notes'])}" if w.get("notes") else ""
            lines.append(f"  • <b>{_html.escape(w['name'])}</b>{atk}{dmg}{notes}")
        await _send_html(update, "\n".join(lines))
        return

    if len(args) < 3:
        await update.message.reply_text(
            f"Uso: /arma {action} <nome> <arma>" + (" [atk] [dano] [notas]" if action == "adicionar" else "")
        )
        return

    name      = args[1].lower()
    rest_args = args[2:]

    if action == "remover":
        weapon_name = " ".join(rest_args).strip()
        try:
            data = remove_weapon(name, weapon_name)
        except (FileNotFoundError, ValueError) as e:
            await update.message.reply_text(str(e))
            return
        char = data["base"]["name"]
        await _send_html(update, f"➖ <b>{_html.escape(char)}</b>: arma <b>{_html.escape(weapon_name)}</b> removida.")
        return

    # adicionar — parse right-to-left: [notas] [dano] [atk] nome_arma
    remaining = list(rest_args)
    notes, atk_bonus, damage = "", "", ""

    if len(remaining) >= 2 and not _DICE_RE.match(remaining[-1]) and not _ATK_RE.match(remaining[-1]):
        notes     = remaining[-1]
        remaining = remaining[:-1]
    if remaining and _DICE_RE.match(remaining[-1]):
        damage    = remaining[-1]
        remaining = remaining[:-1]
    if remaining and _ATK_RE.match(remaining[-1]):
        raw = remaining[-1]
        atk_bonus = raw if raw.startswith(("+", "-")) else f"+{raw}"
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


# ---------------------------------------------------------------------------
# /magias [nome]
# ---------------------------------------------------------------------------

async def magias_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    name = _resolve(update, context.args or [])
    data = load_character(name)
    if data is None:
        await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
        return
    await _send_html(update, format_spells_telegram(data))


# ---------------------------------------------------------------------------
# /magia [nome] <indice>
# ---------------------------------------------------------------------------

async def magia_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_chat_allowed(update):
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /magia [nome] <índice>")
        return

    name, rest_args = _split_name(update, args)
    if not rest_args:
        await update.message.reply_text("Uso: /magia [nome] <índice>")
        return
    try:
        idx = int(rest_args[0])
    except ValueError:
        await update.message.reply_text("Uso: /magia [nome] <índice>")
        return

    data = load_character(name)
    if data is None:
        await update.message.reply_text(f"Ficha de '{_html.escape(name)}' não encontrada.", parse_mode="HTML")
        return
    await _send_html(update, format_spell_detail_telegram(data, idx))


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
    app.add_handler(CommandHandler("item",       item_command))
    app.add_handler(CommandHandler("moeda",      moeda_command))
    app.add_handler(CommandHandler("ca",         ca_command))
    app.add_handler(CommandHandler("arma",       arma_command))
    app.add_handler(CommandHandler("magias",     magias_command))
    app.add_handler(CommandHandler("magia",      magia_command))
    logger.info("Character sheet handlers registered.")
