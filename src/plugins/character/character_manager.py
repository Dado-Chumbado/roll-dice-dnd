import json
import math
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "characters"


def _path(player_name: str) -> Path:
    return _DATA_DIR / f"{player_name.lower()}.json"


def _require(player_name: str) -> dict:
    player_name = player_name.lower()
    data = load_character(player_name)
    if data is None:
        available = list_characters()
        hint = f" Fichas disponíveis: {', '.join(available)}" if available else ""
        raise FileNotFoundError(
            f"Ficha de '{player_name}' não encontrada. Use `!importar` primeiro.{hint}"
        )
    return data


def load_character(player_name: str) -> dict | None:
    p = _path(player_name.lower())
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_character(player_name: str, data: dict) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_path(player_name.lower()), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sync_character(pdf_path: str, player_name: str) -> dict:
    """Import PDF, preserve existing session inventory/notes, save and return."""
    from plugins.character.pdf_extractor import import_pdf

    new_data = import_pdf(pdf_path, player_name)

    existing = load_character(player_name)
    if existing:
        old_session = existing.get("session", {})
        new_data["session"]["inventory"] = old_session.get("inventory", new_data["session"]["inventory"])
        new_data["session"]["notes"]     = old_session.get("notes", "")
        new_data["session"]["currency"]  = old_session.get("currency", new_data["session"]["currency"])

    save_character(player_name, new_data)
    return new_data


def list_characters() -> list[str]:
    if not _DATA_DIR.exists():
        return []
    return [p.stem for p in _DATA_DIR.glob("*.json")]


# ---------------------------------------------------------------------------
# Session management — Phase 2
# ---------------------------------------------------------------------------

def update_hp(player_name: str, delta: int) -> dict:
    """Apply delta to hp_current, clamped to [0, hp_max]."""
    data = _require(player_name)
    hp_max   = data["base"]["hp_max"]
    current  = data["session"]["hp_current"]
    new_hp   = max(0, min(current + delta, hp_max))
    data["session"]["hp_current"] = new_hp
    save_character(player_name, data)
    return data


def use_slot(player_name: str, level: str) -> dict:
    """Mark one spell slot of the given level as used."""
    data = _require(player_name)
    slots_max  = data["base"]["spell_slots_max"]
    slots_used = data["session"].setdefault("spell_slots_used", {})

    if level not in slots_max:
        raise ValueError(f"Nível {level} não existe para este personagem.")

    used  = slots_used.get(level, 0)
    total = slots_max[level]
    if used >= total:
        raise ValueError(f"Sem slots de nível {level} disponíveis (todos usados).")

    slots_used[level] = used + 1
    save_character(player_name, data)
    return data


def reset_slot(player_name: str, level: str) -> dict:
    """Restore all spell slots of the given level."""
    data = _require(player_name)
    if level not in data["base"]["spell_slots_max"]:
        raise ValueError(f"Nível {level} não existe para este personagem.")
    data["session"].setdefault("spell_slots_used", {})[level] = 0
    save_character(player_name, data)
    return data


def rest(player_name: str, rest_type: str) -> dict:
    """curto: recover ceil(hp_max/2). longo: full hp + all slots restored."""
    data = _require(player_name)
    hp_max = data["base"]["hp_max"]

    if rest_type == "longo":
        data["session"]["hp_current"] = hp_max
        data["session"]["temp_hp"]    = 0
        data["session"]["spell_slots_used"] = {
            lvl: 0 for lvl in data["base"]["spell_slots_max"]
        }
    elif rest_type == "curto":
        current  = data["session"]["hp_current"]
        recovery = math.ceil(hp_max / 2)
        data["session"]["hp_current"] = min(current + recovery, hp_max)
    else:
        raise ValueError("Tipo inválido. Use `curto` ou `longo`.")

    save_character(player_name, data)
    return data


# PT-BR coin abbreviation → internal JSON key
_COIN_ALIASES: dict[str, str] = {
    "pc": "cp",   # cobre
    "pp": "sp",   # prata (PT-BR "pp" = peças de prata → stored as "sp")
    "pe": "ep",   # electrum
    "po": "gp",   # ouro
    "ppl": "pp",  # platina (stored as "pp" in D&D standard)
    # also accept internal keys directly
    "cp": "cp", "sp": "sp", "ep": "ep", "gp": "gp",
}

COIN_LABELS: dict[str, str] = {
    "pp": "PPl", "gp": "PO", "ep": "PE", "sp": "PP", "cp": "PC",
}


def resolve_coin(coin_abbr: str) -> str:
    """Normalize a PT-BR or standard coin abbreviation to internal key. Raises ValueError if unknown."""
    key = _COIN_ALIASES.get(coin_abbr.lower())
    if key is None:
        raise ValueError(
            f"Moeda '{coin_abbr}' desconhecida. Use: pc, pp, pe, po, ppl."
        )
    return key


def update_currency(player_name: str, coin_abbr: str, delta: int) -> dict:
    """Add delta coins of the given denomination (clamped to >= 0)."""
    data = _require(player_name)
    key = resolve_coin(coin_abbr)
    currency = data["session"].setdefault("currency", {})
    current = currency.get(key, 0)
    currency[key] = max(0, current + delta)
    save_character(player_name, data)
    return data


def set_ca(player_name: str, value: int) -> dict:
    """Manually override the character's AC."""
    if value < 0:
        raise ValueError("CA não pode ser negativa.")
    data = _require(player_name)
    data["base"]["ac"] = value
    save_character(player_name, data)
    return data


def add_weapon(player_name: str, name: str, atk_bonus: str = "", damage: str = "", notes: str = "") -> dict:
    """Add a weapon to the character's attack list."""
    data = _require(player_name)
    attacks = data["base"].setdefault("attacks", [])
    attacks.append({"name": name, "atk_bonus": atk_bonus, "damage": damage, "notes": notes})
    save_character(player_name, data)
    return data


def remove_weapon(player_name: str, weapon_name: str) -> dict:
    """Remove a weapon by name (case-insensitive). Raises ValueError if not found."""
    data = _require(player_name)
    attacks = data["base"].get("attacks", [])
    lower = weapon_name.lower()
    original = [w for w in attacks if w["name"].lower() == lower]
    if not original:
        raise ValueError(f"Arma '{weapon_name}' não encontrada.")
    data["base"]["attacks"] = [w for w in attacks if w["name"].lower() != lower]
    save_character(player_name, data)
    return data


def update_inventory(player_name: str, item_name: str, qty: int, add: bool) -> dict:
    """Add or remove items from the session inventory."""
    data      = _require(player_name)
    inventory = data["session"]["inventory"]

    item_name_lower = item_name.lower()

    if add:
        for item in inventory:
            if item["name"].lower() == item_name_lower:
                item["qty"] += qty
                save_character(player_name, data)
                return data
        inventory.append({"name": item_name, "qty": qty, "weight": None})
    else:
        for item in inventory:
            if item["name"].lower() == item_name_lower:
                item["qty"] -= qty
                if item["qty"] <= 0:
                    inventory.remove(item)
                save_character(player_name, data)
                return data
        raise ValueError(f"Item '{item_name}' não encontrado no inventário.")

    save_character(player_name, data)
    return data
