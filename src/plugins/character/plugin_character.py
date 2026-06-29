import os
import re
import tempfile
import logging

from config import ConfigManager
from plugin_manager import Plugin
from plugins.character.character_manager import (
    sync_character, load_character, list_characters,
    update_hp, use_slot, reset_slot, rest, update_inventory,
    update_currency, set_ca, add_weapon, remove_weapon,
    COIN_LABELS, resolve_coin,
)
from plugins.character.sheet_formatter import format_sheet, format_spells, format_spell_detail

logger = logging.getLogger(__name__)
current_folder = os.path.dirname(__file__)


def _sign(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)


def _hp_bar(current: int, maximum: int, width: int = 10) -> str:
    if maximum <= 0:
        return ""
    ratio = max(0, min(current / maximum, 1))
    filled = round(ratio * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _split_message(text: str, limit: int = 1900) -> list[str]:
    chunks, current, current_len = [], [], 0
    for line in text.split("\n"):
        if current_len + len(line) + 1 > limit:
            chunks.append("\n".join(current))
            current, current_len = [line], len(line)
        else:
            current.append(line)
            current_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks


def _resolve_name(ctx, player_name: str | None) -> str:
    return (player_name or ctx.author.display_name).lower()


class PluginCharacter(Plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.cm = ConfigManager(os.path.join(current_folder, "plugin_config.json"))
        self.commands_plugin(bot)
        logger.info(f"{self.__class__.__name__} initialized!")

    def commands_plugin(self, bot):

        # ------------------------------------------------------------------
        # !importar <nome>  (PDF em anexo)
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "sync"),
            help=self.cm.get_description("character", "sync"),
        )
        async def importar(ctx, player_name: str = None):
            if not player_name:
                await ctx.send("Uso: `!importar <nome>` com o PDF da ficha em anexo.")
                return
            if not ctx.message.attachments:
                await ctx.send("Anexe o PDF exportado do D&D Beyond à mensagem.")
                return
            attachment = ctx.message.attachments[0]
            if not attachment.filename.lower().endswith(".pdf"):
                await ctx.send("O arquivo deve ser um PDF exportado do D&D Beyond.")
                return

            player_name = player_name.lower()
            async with ctx.typing():
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    await attachment.save(tmp_path)
                    data = sync_character(tmp_path, player_name)
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

            b = data["base"]
            await ctx.send(
                f"✅ **{b['name']}** sincronizado! "
                f"{b['class']} {b['level']} | HP máx: {b['hp_max']}\n"
                f"Use `!ficha {player_name}` para ver a ficha."
            )

        # ------------------------------------------------------------------
        # !ficha [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "ficha"),
            help=self.cm.get_description("character", "ficha"),
        )
        async def ficha(ctx, first: str = None, second: str = None):
            # !ficha                    → simples, nome = display_name
            # !ficha completa           → completa, nome = display_name
            # !ficha <nome>             → simples, nome = first
            # !ficha completa <nome>    → completa, nome = second
            if first and first.lower() == "completa":
                mode = "completa"
                name = _resolve_name(ctx, second)
            else:
                mode = "simples"
                name = _resolve_name(ctx, first)

            data = load_character(name)
            if data is None:
                available = list_characters()
                hint = f" Fichas disponíveis: {', '.join(available)}" if available else ""
                await ctx.send(
                    f"Ficha de **{name}** não encontrada.{hint}\n"
                    f"Use `!importar {name}` para importar o PDF."
                )
                return
            sheet = format_sheet(data, mode=mode)
            for chunk in _split_message(sheet):
                await ctx.send(chunk)

        # ------------------------------------------------------------------
        # !hp <delta> [nome]   ex: !hp -8   !hp +4   !hp 10
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "hp"),
            help=self.cm.get_description("character", "hp"),
        )
        async def hp(ctx, delta_str: str, player_name: str = None):
            try:
                delta = int(delta_str)
            except ValueError:
                await ctx.send("Uso: `!hp -8` ou `!hp +4`")
                return
            name = _resolve_name(ctx, player_name)
            try:
                data = update_hp(name, delta)
            except FileNotFoundError as e:
                await ctx.send(str(e))
                return

            session = data["session"]
            hp_cur  = session["hp_current"]
            hp_max  = data["base"]["hp_max"]
            char    = data["base"]["name"]
            bar     = _hp_bar(hp_cur, hp_max)
            verb    = "recuperou" if delta >= 0 else "sofreu"
            await ctx.send(
                f"{'❤️' if delta >= 0 else '🩸'} **{char}** {verb} "
                f"**{abs(delta)} HP** — "
                f"HP: **{hp_cur}/{hp_max}** {bar}"
            )

        # ------------------------------------------------------------------
        # !slot <nivel> [reset] [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "slot"),
            help=self.cm.get_description("character", "slot"),
        )
        async def slot(ctx, level: str, action: str = None, player_name: str = None):
            is_reset = action and action.lower() == "reset"
            if action and not is_reset:
                player_name = action
            name = _resolve_name(ctx, player_name)
            try:
                if is_reset:
                    data = reset_slot(name, level)
                    msg_prefix = f"🔄 Slots de nível **{level}** restaurados"
                else:
                    data = use_slot(name, level)
                    msg_prefix = f"✨ Slot de nível **{level}** usado"
            except (FileNotFoundError, ValueError) as e:
                await ctx.send(str(e))
                return

            slots_max  = data["base"]["spell_slots_max"]
            slots_used = data["session"]["spell_slots_used"]
            used  = slots_used.get(level, 0)
            total = slots_max.get(level, 0)
            pips  = "◆" * (total - used) + "◇" * used
            await ctx.send(f"{msg_prefix} — Nível {level}: {pips} ({total - used}/{total})")

        # ------------------------------------------------------------------
        # !slots [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "slots"),
            help=self.cm.get_description("character", "slots"),
        )
        async def slots(ctx, player_name: str = None):
            name = _resolve_name(ctx, player_name)
            data = load_character(name)
            if data is None:
                await ctx.send(f"Ficha de **{name}** não encontrada.")
                return

            slots_max  = data["base"].get("spell_slots_max", {})
            slots_used = data["session"].get("spell_slots_used", {})
            char = data["base"]["name"]

            if not slots_max:
                await ctx.send(f"**{char}** não possui slots de magia.")
                return

            lines = [f"✨ **Slots de magia — {char}**"]
            for lvl in sorted(slots_max.keys(), key=int):
                total     = slots_max[lvl]
                used      = slots_used.get(lvl, 0)
                remaining = total - used
                pips      = "◆" * remaining + "◇" * used
                lines.append(f"  Nível {lvl}: {pips} ({remaining}/{total})")
            await ctx.send("\n".join(lines))

        # ------------------------------------------------------------------
        # !descanso <curto|longo> [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "descanso"),
            help=self.cm.get_description("character", "descanso"),
        )
        async def descanso(ctx, tipo: str = None, player_name: str = None):
            if tipo not in ("curto", "longo"):
                await ctx.send("Uso: `!descanso curto` ou `!descanso longo`")
                return
            name = _resolve_name(ctx, player_name)
            try:
                data = rest(name, tipo)
            except (FileNotFoundError, ValueError) as e:
                await ctx.send(str(e))
                return

            char   = data["base"]["name"]
            hp_cur = data["session"]["hp_current"]
            hp_max = data["base"]["hp_max"]
            bar    = _hp_bar(hp_cur, hp_max)
            emoji  = "🌙" if tipo == "longo" else "💤"
            await ctx.send(
                f"{emoji} **{char}** descansou ({tipo})! "
                f"HP: **{hp_cur}/{hp_max}** {bar}"
            )

        # ------------------------------------------------------------------
        # !inventario [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "inventario"),
            help=self.cm.get_description("character", "inventario"),
        )
        async def inventario(ctx, player_name: str = None):
            name = _resolve_name(ctx, player_name)
            data = load_character(name)
            if data is None:
                await ctx.send(f"Ficha de **{name}** não encontrada.")
                return

            char      = data["base"]["name"]
            inventory = data["session"]["inventory"]
            currency  = data["session"].get("currency", {})

            if not inventory:
                await ctx.send(f"🎒 **{char}** não possui itens no inventário.")
                return

            lines = [f"🎒 **Inventário — {char}**"]
            for item in inventory:
                qty    = item.get("qty", 1)
                weight = item.get("weight")
                w_str  = f" ({weight})" if weight and weight != "--" else ""
                lines.append(f"  • {item['name']} x{qty}{w_str}")

            coins = []
            for k, label in [("pp", "PPl"), ("gp", "PO"), ("ep", "PE"), ("sp", "PP"), ("cp", "PC")]:
                v = currency.get(k, 0)
                if v:
                    coins.append(f"{v} {label}")
            if coins:
                lines.append(f"\n💰 **Moedas:** {' | '.join(coins)}")

            for chunk in _split_message("\n".join(lines)):
                await ctx.send(chunk)

        # ------------------------------------------------------------------
        # !item <adicionar|remover> <nome> [qty] [player]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "item"),
            help=self.cm.get_description("character", "item"),
        )
        async def item(ctx, action: str = None, *, args: str = ""):
            if action not in ("adicionar", "remover"):
                await ctx.send(
                    "Uso: `!item adicionar <nome_item> [qty] [jogador]` ou `!item remover <nome_item> [qty] [jogador]`"
                )
                return

            # Parse from right: [jogador] [qty] item_name
            # Strategy: check if last word matches an existing character; if so, it's the player name.
            # Then check if remaining last word is a digit (qty).
            tokens = args.strip().split()
            if not tokens:
                await ctx.send("Informe o nome do item.")
                return

            player_name = None
            qty = 1

            # Check if last token is a known character name
            if len(tokens) >= 2 and load_character(tokens[-1]):
                player_name = tokens[-1].lower()
                tokens = tokens[:-1]

            # Check if new last token is a quantity
            if len(tokens) >= 2 and tokens[-1].isdigit():
                qty = int(tokens[-1])
                tokens = tokens[:-1]

            item_name = " ".join(tokens).strip()

            if not item_name:
                await ctx.send("Informe o nome do item.")
                return

            name = _resolve_name(ctx, player_name)
            try:
                data = update_inventory(name, item_name, qty, add=(action == "adicionar"))
            except (FileNotFoundError, ValueError) as e:
                await ctx.send(str(e))
                return

            char  = data["base"]["name"]
            emoji = "➕" if action == "adicionar" else "➖"
            verb  = "adicionado" if action == "adicionar" else "removido"
            await ctx.send(f"{emoji} **{char}**: {item_name} x{qty} {verb}.")

        # ------------------------------------------------------------------
        # !moeda <+/-delta> <tipo> [nome]   ex: !moeda +10 po   !moeda -3 pp trovao
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "moeda"),
            help=self.cm.get_description("character", "moeda"),
        )
        async def moeda(ctx, delta_str: str = None, coin_abbr: str = None, player_name: str = None):
            if not delta_str or not coin_abbr:
                await ctx.send("Uso: `!moeda +10 po [nome]`  (tipos: pc, pp, pe, po, ppl)")
                return
            try:
                delta = int(delta_str)
            except ValueError:
                await ctx.send("Uso: `!moeda +10 po [nome]`  (tipos: pc, pp, pe, po, ppl)")
                return
            try:
                key = resolve_coin(coin_abbr)
            except ValueError as e:
                await ctx.send(str(e))
                return
            name = _resolve_name(ctx, player_name)
            try:
                data = update_currency(name, coin_abbr, delta)
            except FileNotFoundError as e:
                await ctx.send(str(e))
                return

            char     = data["base"]["name"]
            currency = data["session"].get("currency", {})
            new_val  = currency.get(key, 0)
            label    = COIN_LABELS.get(key, coin_abbr.upper())
            verb     = "recebeu" if delta >= 0 else "gastou"
            await ctx.send(
                f"💰 **{char}** {verb} **{abs(delta)} {label}** — "
                f"saldo: **{new_val} {label}**"
            )

        # ------------------------------------------------------------------
        # !ca <valor> [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "ca"),
            help=self.cm.get_description("character", "ca"),
        )
        async def ca(ctx, value_str: str = None, player_name: str = None):
            if not value_str:
                await ctx.send("Uso: `!ca <valor> [nome]`")
                return
            try:
                value = int(value_str)
            except ValueError:
                await ctx.send("Uso: `!ca <valor> [nome]`")
                return
            name = _resolve_name(ctx, player_name)
            try:
                data = set_ca(name, value)
            except (FileNotFoundError, ValueError) as e:
                await ctx.send(str(e))
                return
            char = data["base"]["name"]
            await ctx.send(f"🛡️ **{char}** — CA atualizada para **{value}**")

        # ------------------------------------------------------------------
        # !arma adicionar <nome> [atk] [dano] [notas] [jogador]
        # !arma remover <nome> [jogador]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "arma"),
            help=self.cm.get_description("character", "arma"),
        )
        async def arma(ctx, action: str = None, *, args: str = ""):
            if action not in ("adicionar", "remover", "listar"):
                await ctx.send(
                    "Uso:\n"
                    "`!arma adicionar <nome> [atk] [dano] [notas] [jogador]`\n"
                    "`!arma remover <nome> [jogador]`\n"
                    "`!arma listar [jogador]`"
                )
                return

            tokens = args.strip().split()

            if action == "listar":
                name = _resolve_name(ctx, tokens[0] if tokens else None)
                data = load_character(name)
                if data is None:
                    await ctx.send(f"Ficha de **{name}** não encontrada.")
                    return
                attacks = data["base"].get("attacks", [])
                char = data["base"]["name"]
                if not attacks:
                    await ctx.send(f"**{char}** não possui armas cadastradas.")
                    return
                lines = [f"⚔️ **Armas — {char}**"]
                for w in attacks:
                    atk   = f" | Atk: {w['bonus']}" if w.get("bonus") else ""
                    dmg   = f" | Dano: {w['damage']}" if w.get("damage") else ""
                    notes = f" | {w['notes']}" if w.get("notes") else ""
                    lines.append(f"  • **{w['name']}**{atk}{dmg}{notes}")
                await ctx.send("\n".join(lines))
                return

            if action == "remover":
                # Last token may be a player name
                player_name = None
                if len(tokens) >= 2 and load_character(tokens[-1]):
                    player_name = tokens[-1].lower()
                    tokens = tokens[:-1]
                weapon_name = " ".join(tokens).strip()
                if not weapon_name:
                    await ctx.send("Informe o nome da arma.")
                    return
                name = _resolve_name(ctx, player_name)
                try:
                    data = remove_weapon(name, weapon_name)
                except (FileNotFoundError, ValueError) as e:
                    await ctx.send(str(e))
                    return
                char = data["base"]["name"]
                await ctx.send(f"➖ **{char}**: arma **{weapon_name}** removida.")
                return

            # action == "adicionar"
            # Parse tokens right-to-left:
            #   [jogador] if matches a character file
            #   [notas]   if not matching +/-num or NdN pattern (grabbed greedily from end)
            #   [dano]    if matches dice pattern
            #   [atk]     if starts with + or -
            #   rest      = weapon name

            if not tokens:
                await ctx.send("Informe o nome da arma.")
                return

            player_name = None
            if len(tokens) >= 2 and load_character(tokens[-1]):
                player_name = tokens[-1].lower()
                tokens = tokens[:-1]

            notes = ""
            atk_bonus = ""
            damage = ""

            # Check if last token looks like notes (not a dice expr and not +/- number)
            import re as _re
            dice_re = _re.compile(r'^\d*d\d+', _re.IGNORECASE)
            atk_re  = _re.compile(r'^[+-]\d+$')

            # Consume from right: notes (any free text after damage/atk)
            # Simple heuristic: if last non-player token doesn't look like dice/atk → notes
            remaining = list(tokens)
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
                await ctx.send("Informe o nome da arma.")
                return

            name = _resolve_name(ctx, player_name)
            try:
                data = add_weapon(name, weapon_name, atk_bonus, damage, notes)
            except FileNotFoundError as e:
                await ctx.send(str(e))
                return

            char  = data["base"]["name"]
            parts = [f"**{weapon_name}**"]
            if atk_bonus:
                parts.append(f"Atk: {atk_bonus}")
            if damage:
                parts.append(f"Dano: {damage}")
            if notes:
                parts.append(notes)
            await ctx.send(f"➕ **{char}**: {' | '.join(parts)} adicionada.")

        # ------------------------------------------------------------------
        # !magias [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "magias"),
            help=self.cm.get_description("character", "magias"),
        )
        async def magias(ctx, player_name: str = None):
            name = _resolve_name(ctx, player_name)
            data = load_character(name)
            if data is None:
                await ctx.send(f"Ficha de **{name}** não encontrada.")
                return
            sheet = format_spells(data)
            for chunk in _split_message(sheet):
                await ctx.send(chunk)

        # ------------------------------------------------------------------
        # !magia <indice> [nome]
        # ------------------------------------------------------------------
        @bot.command(
            name=self.cm.get_prefix("character", "magia"),
            help=self.cm.get_description("character", "magia"),
        )
        async def magia(ctx, index: str = None, player_name: str = None):
            if index is None:
                await ctx.send("Uso: `!magia <índice> [nome]` — veja os índices com `!magias`")
                return
            try:
                idx = int(index)
            except ValueError:
                await ctx.send("Uso: `!magia <índice> [nome]` — veja os índices com `!magias`")
                return
            name = _resolve_name(ctx, player_name)
            data = load_character(name)
            if data is None:
                await ctx.send(f"Ficha de **{name}** não encontrada.")
                return
            await ctx.send(format_spell_detail(data, idx))
