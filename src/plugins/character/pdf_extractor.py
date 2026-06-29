import os
import re
from datetime import datetime, timezone
import pypdf

# ---------------------------------------------------------------------------
# Dictionary translations — applied at import time, stored in JSON
# ---------------------------------------------------------------------------

_DAMAGE_TYPE_PT = {
    "Piercing": "Perfurante", "Slashing": "Cortante", "Bludgeoning": "Contundente",
    "Fire": "Fogo", "Cold": "Frio", "Lightning": "Elétrico", "Thunder": "Trovão",
    "Acid": "Ácido", "Poison": "Veneno", "Necrotic": "Necrótico", "Radiant": "Radiante",
    "Psychic": "Psíquico", "Force": "Força", "Magical": "Mágico",
}

_SPEED_TYPE_PT = {
    "Walking": "Caminhando", "Flying": "Voando", "Swimming": "Nadando",
    "Climbing": "Escalando", "Burrowing": "Escavando",
}

_CAST_TIME_PT = {
    "1 Action": "1 Ação", "1 Bonus Action": "1 Ação Bônus",
    "1 Reaction": "1 Reação", "1 Minute": "1 Minuto", "10 Minutes": "10 Minutos",
    "1 Hour": "1 Hora", "8 Hours": "8 Horas", "24 Hours": "24 Horas",
}

_RANGE_PT = {
    "Self": "Si mesmo", "Touch": "Toque", "Sight": "Visão",
    "Unlimited": "Ilimitado", "Special": "Especial",
}

_DURATION_PT = {
    "Instantaneous": "Instantâneo", "Permanent": "Permanente", "Special": "Especial",
    "Until dispelled": "Até ser dissipado", "Until dispelled or triggered": "Até ser dissipado ou ativado",
    "Concentration, up to 1 round": "Concentração, até 1 rodada",
    "Concentration, up to 1 minute": "Concentração, até 1 minuto",
    "Concentration, up to 10 minutes": "Concentração, até 10 minutos",
    "Concentration, up to 1 hour": "Concentração, até 1 hora",
    "Concentration, up to 2 hours": "Concentração, até 2 horas",
    "Concentration, up to 8 hours": "Concentração, até 8 horas",
    "Concentration, up to 24 hours": "Concentração, até 24 horas",
    "1 round": "1 rodada", "6 rounds": "6 rodadas",
    "1 minute": "1 minuto", "10 minutes": "10 minutos",
    "1 hour": "1 hora", "2 hours": "2 horas", "8 hours": "8 horas",
    "24 hours": "24 horas", "7 days": "7 dias", "10 days": "10 dias",
    "30 days": "30 dias",
}

_ALIGNMENT_PT = {
    "Lawful Good": "Leal e Bom", "Neutral Good": "Neutro e Bom",
    "Chaotic Good": "Caótico e Bom", "Lawful Neutral": "Leal e Neutro",
    "True Neutral": "Neutro Verdadeiro", "Neutral": "Neutro",
    "Chaotic Neutral": "Caótico e Neutro", "Lawful Evil": "Leal e Mau",
    "Neutral Evil": "Neutro e Mau", "Chaotic Evil": "Caótico e Mau",
}

_CLASS_PT = {
    "Barbarian": "Bárbaro", "Bard": "Bardo", "Cleric": "Clérigo",
    "Druid": "Druida", "Fighter": "Guerreiro", "Monk": "Monge",
    "Paladin": "Paladino", "Ranger": "Patrulheiro", "Rogue": "Ladino",
    "Sorcerer": "Feiticeiro", "Warlock": "Bruxo", "Wizard": "Mago",
    "Artificer": "Artífice", "Blood Hunter": "Caçador de Sangue",
}


def _translate_class(raw: str) -> str:
    """Translate class name(s), preserving level numbers and multiclass separators.
    'Druid 3' → 'Druida 3'   'Fighter 5 / Wizard 3' → 'Guerreiro 5 / Mago 3'
    """
    if not raw:
        return raw
    def _replace(m):
        return _CLASS_PT.get(m.group(0), m.group(0))
    return re.sub(r'\b(' + '|'.join(re.escape(k) for k in _CLASS_PT) + r')\b', _replace, raw)


_SIZE_PT = {
    "Tiny": "Minúsculo", "Small": "Pequeno", "Medium": "Médio",
    "Large": "Grande", "Huge": "Enorme", "Gargantuan": "Colossal",
}

_RACE_PT = {
    "Human": "Humano", "Elf": "Elfo", "High Elf": "Alto Elfo",
    "Wood Elf": "Elfo da Floresta", "Dark Elf": "Elfo Negro", "Drow": "Drow",
    "Dwarf": "Anão", "Hill Dwarf": "Anão das Colinas", "Mountain Dwarf": "Anão das Montanhas",
    "Halfling": "Halfling", "Lightfoot Halfling": "Halfling Pés-Leves",
    "Stout Halfling": "Halfling Robusto", "Gnome": "Gnomo",
    "Forest Gnome": "Gnomo da Floresta", "Rock Gnome": "Gnomo das Rochas",
    "Half-Elf": "Meio-Elfo", "Half-Orc": "Meio-Orc",
    "Tiefling": "Tiefling", "Dragonborn": "Draconato",
    "Aasimar": "Aasimar", "Goliath": "Goliath", "Tabaxi": "Tabaxi",
    "Kenku": "Kenku", "Firbolg": "Firbolg", "Lizardfolk": "Homem-Lagarto",
    "Triton": "Tritão", "Yuan-Ti Pureblood": "Yuan-Ti Sangue Puro",
    "Bugbear": "Bugbear", "Goblin": "Goblin", "Hobgoblin": "Hobgoblin",
    "Kobold": "Kobold", "Orc": "Orc", "Tortle": "Tortle",
    "Changeling": "Mutante", "Kalashtar": "Kalashtar", "Shifter": "Mutante-Fera",
    "Warforged": "Forjado", "Centaur": "Centauro", "Loxodon": "Loxodonte",
    "Minotaur": "Minotauro", "Simic Hybrid": "Híbrido Simic", "Vedalken": "Vedalken",
    "Leonin": "Leonino", "Satyr": "Sátiro", "Fairy": "Fada",
    "Harengon": "Harengon", "Owlin": "Owlin",
}

_BACKGROUND_PT = {
    "Acolyte": "Acólito", "Charlatan": "Charlatão", "Criminal": "Criminoso",
    "Spy": "Espião", "Entertainer": "Artista", "Gladiator": "Gladiador",
    "Folk Hero": "Herói do Povo", "Guild Artisan": "Artesão de Guilda",
    "Guild Merchant": "Mercador de Guilda", "Hermit": "Eremita", "Noble": "Nobre",
    "Knight": "Cavaleiro", "Outlander": "Forasteiro", "Sage": "Sábio",
    "Sailor": "Marinheiro", "Pirate": "Pirata", "Soldier": "Soldado",
    "Urchin": "Criança de Rua", "Haunted One": "Assombrado",
    "City Watch": "Guarda da Cidade", "Clan Crafter": "Artesão do Clã",
    "Cloistered Scholar": "Estudioso Enclausurado", "Courtier": "Cortesão",
    "Faction Agent": "Agente de Facção", "Far Traveler": "Viajante Distante",
    "Inheritor": "Herdeiro", "Knight of the Order": "Cavaleiro da Ordem",
    "Mercenary Veteran": "Veterano Mercenário", "Urban Bounty Hunter": "Caçador de Recompensas Urbano",
    "Waterdhavian Noble": "Nobre de Água Funda", "Witchlight Hand": "Ajudante da Luz Feiticeira",
    "Athlete": "Atleta", "Feylost": "Perdido no Feywild",
    "Rewarded": "Recompensado", "Ruined": "Arruinado",
    "Wildspacer": "Viajante do Espaço Selvagem",
}


def _dict_translate(value: str, table: dict) -> str:
    """Exact-match lookup; returns original if not found."""
    return table.get(value, value)


def _translate_speed(speed: str) -> str:
    result = speed.replace(" ft.", " pés")
    for en, pt in _SPEED_TYPE_PT.items():
        result = result.replace(en, pt)
    return result


def _translate_damage(damage: str) -> str:
    if not damage:
        return damage
    for en, pt in _DAMAGE_TYPE_PT.items():
        damage = damage.replace(en, pt)
    return damage


def _translate_range(r: str) -> str:
    if not r:
        return r
    result = _RANGE_PT.get(r, r)
    result = result.replace(" ft.", " pés")
    return result


def _deepl_translate_batch(texts: list[str], api_key: str) -> list[str]:
    """Translate a list of strings EN→PT-BR via DeepL in a single API call.
    Returns the list unchanged if any error occurs."""
    import deepl
    try:
        translator = deepl.Translator(api_key)
        results = translator.translate_text(texts, source_lang="EN", target_lang="PT-BR")
        return [r.text for r in results]
    except Exception:
        return texts

# ---------------------------------------------------------------------------
# Field names extracted by inspecting PUR0O550_141918267.pdf (Barbarian 3).
# Pages 2-4 repeat header fields with suffixes (e.g. CharacterName2).
# We read page 1 for most stats and deduplicate across pages.
# ---------------------------------------------------------------------------

_SKILL_FIELDS = [
    ("Acrobatics",    "AcrobaticsProf",    "Acrobatics",    "AcrobaticsMod"),
    ("AnimalHandling","AnimalHandlingProf", "Animal",        "AnimalMod"),
    ("Arcana",        "ArcanaProf",        "Arcana",        "ArcanaMod"),
    ("Athletics",     "AthleticsProf",     "Athletics",     "AthleticsMod"),
    ("Deception",     "DeceptionProf",     "Deception",     "DeceptionMod"),
    ("History",       "HistoryProf",       "History",       "HistoryMod"),
    ("Insight",       "InsightProf",       "Insight",       "InsightMod"),
    ("Intimidation",  "IntimidationProf",  "Intimidation",  "IntimidationMod"),
    ("Investigation", "InvestigationProf", "Investigation", "InvestigationMod"),
    ("Medicine",      "MedicineProf",      "Medicine",      "MedicineMod"),
    ("Nature",        "NatureProf",        "Nature",        "NatureMod"),
    ("Perception",    "PerceptionProf",    "Perception",    "PerceptionMod"),
    ("Performance",   "PerformanceProf",   "Performance",   "PerformanceMod"),
    ("Persuasion",    "PersuasionProf",    "Persuasion",    "PersuasionMod"),
    ("Religion",      "ReligionProf",      "Religion",      "ReligionMod"),
    ("SleightOfHand", "SleightOfHandProf", "SleightofHand", "SleightofHandMod"),
    ("Stealth",       "StealthProf",       "Stealth",       "StealthMod"),
    ("Survival",      "SurvivalProf",      "Survival",      "SurvivalMod"),
]

_SAVE_FIELDS = [
    ("strength",     "StrProf",  "ST Strength"),
    ("dexterity",    "DexProf",  "ST Dexterity"),
    ("constitution", "ConProf",  "ST Constitution"),
    ("intelligence", "IntProf",  "ST Intelligence"),
    ("wisdom",       "WisProf",  "ST Wisdom"),
    ("charisma",     "ChaProf",  "ST Charisma"),
]

_ATTR_FIELDS = [
    ("strength",     "STR",  "STRmod"),
    ("dexterity",    "DEX",  "DEXmod"),
    ("constitution", "CON",  "CONmod"),
    ("intelligence", "INT",  "INTmod"),
    ("wisdom",       "WIS",  "WISmod"),
    ("charisma",     "CHA",  "CHamod"),
]


def _get_all_fields(pdf_path: str) -> dict:
    """Return {field_name: value} for every Widget annotation in the PDF.
    Duplicate field names (page repetitions with suffix 2/3/4) are skipped
    — first occurrence wins.
    """
    reader = pypdf.PdfReader(pdf_path)
    fields = {}
    for page in reader.pages:
        annots_ref = page.get("/Annots")
        if not annots_ref:
            continue
        annots = annots_ref.get_object()
        if not isinstance(annots, list):
            annots = [annots]
        for ref in annots:
            annot = ref.get_object() if hasattr(ref, "get_object") else ref
            if str(annot.get("/Subtype")) != "/Widget":
                continue
            name = str(annot.get("/T", "")).strip()
            value = str(annot.get("/V", "")).strip()
            if name and name not in fields:
                fields[name] = value
    return fields


def _int(v: str, default: int = 0) -> int:
    try:
        return int(v.strip())
    except (ValueError, AttributeError):
        return default


def _modifier(v: str, default: int = 0) -> int:
    """'+4' → 4, '-1' → -1, '' → 0"""
    v = v.strip()
    try:
        return int(v)
    except (ValueError, AttributeError):
        return default


def _is_proficient(v: str) -> bool:
    return v.strip() in ("•", "P", "Yes", "X", "x")


def _parse_class_level(raw: str) -> tuple[str, int, str | None]:
    """'Barbarian 3' → ('Barbarian', 3, None)
    'Fighter 5 / Wizard 3' → ('Fighter', 5, 'Fighter 5 / Wizard 3')
    Returns (primary_class, primary_level, multiclass_raw_or_None)
    """
    raw = raw.strip()
    # Multiclass: contains '/' e.g. "Fighter 5/Wizard 3"
    if "/" in raw:
        first = raw.split("/")[0].strip()
    else:
        first = raw

    m = re.match(r"^(.+?)\s+(\d+)\s*$", first)
    if m:
        return m.group(1).strip(), int(m.group(2)), (raw if "/" in raw else None)
    return raw, 1, None


def _build_attacks(fields: dict) -> list:
    attacks = []
    for i in range(1, 7):
        if i == 1:
            name_key, atk_key, dmg_key, notes_key = "Wpn Name", "Wpn1 AtkBonus", "Wpn1 Damage", "Wpn Notes 1"
        else:
            name_key  = f"Wpn Name {i}"
            atk_key   = f"Wpn{i} AtkBonus"
            dmg_key   = f"Wpn{i} Damage"
            notes_key = f"Wpn Notes {i}"
        name = fields.get(name_key, "").strip()
        if not name:
            continue
        attacks.append({
            "name":   name,
            "bonus":  fields.get(atk_key, "").strip() or None,
            "damage": _translate_damage(fields.get(dmg_key, "").strip()) or None,
            "notes":  fields.get(notes_key, "").strip() or None,
        })
    return attacks


def _build_equipment(fields: dict) -> list:
    items = []
    # Equipment fields: Eq Name0..N, Eq Qty0..N
    i = 0
    while True:
        name = fields.get(f"Eq Name{i}", "").strip()
        if not name:
            break
        qty_str = fields.get(f"Eq Qty{i}", "1").strip()
        weight  = fields.get(f"Eq Weight{i}", "").strip()
        try:
            qty = int(qty_str)
        except ValueError:
            qty = 1
        items.append({"name": name, "qty": qty, "weight": weight or None})
        i += 1
    return items


def _build_spells(fields: dict) -> list:
    spells = []
    # Pattern 1: spellNameN, spellPreparedN, spellSource0 etc.
    i = 0
    while True:
        name = fields.get(f"spellName{i}", "").strip()
        if not name:
            break
        prepared = fields.get(f"spellPrepared{i}", "").strip() not in ("", "O")
        level_raw = fields.get(f"spellHeader1", "").strip()  # e.g. "=== 1st LEVEL ==="
        spells.append({
            "name":       name,
            "prepared":   prepared,
            "save_hit":   fields.get(f"spellSaveHit{i}", "").strip() or None,
            "cast_time":  _dict_translate(fields.get(f"spellCastingTime{i}", "").strip(), _CAST_TIME_PT) or None,
            "range":      _translate_range(fields.get(f"spellRange{i}", "").strip()) or None,
            "components": fields.get(f"spellComponents{i}", "").strip() or None,
            "duration":   _dict_translate(fields.get(f"spellDuration{i}", "").strip(), _DURATION_PT) or None,
            "source":     fields.get(f"spellSource{i}", "").strip() or None,
            "notes":      fields.get(f"spellNotes{i}", "").strip() or None,
        })
        i += 1
    # Pattern 2: SpellNameN (alternate rows)
    i = 3
    while True:
        name = fields.get(f"SpellName{i}", "").strip()
        if not name:
            break
        prepared = fields.get(f"Prepared{i}", "").strip() not in ("", "O")
        spells.append({
            "name":       name,
            "prepared":   prepared,
            "save_hit":   fields.get(f"SaveHit{i}", "").strip() or None,
            "cast_time":  _dict_translate(fields.get(f"CastingTime{i}", "").strip(), _CAST_TIME_PT) or None,
            "range":      _translate_range(fields.get(f"Range{i}", "").strip()) or None,
            "components": fields.get(f"Components{i}", "").strip() or None,
            "duration":   _dict_translate(fields.get(f"Duration{i}", "").strip(), _DURATION_PT) or None,
            "source":     fields.get(f"Source{i}", "").strip() or None,
            "notes":      fields.get(f"Notes{i}", "").strip() or None,
        })
        i += 1
    return spells


def _build_spell_slots(fields: dict) -> dict:
    """Extract spell slot totals from spellSlotHeaderN fields.
    The field typically contains a string like '4 / 4' or is empty.
    Returns {level_str: max_slots} for non-empty levels.
    """
    slots = {}
    for lvl in range(1, 10):
        raw = fields.get(f"spellSlotHeader{lvl}", "").strip()
        if not raw:
            continue
        # Try to parse "4 / 4", "4/4", or just "4"
        m = re.match(r"(\d+)", raw)
        if m:
            slots[str(lvl)] = int(m.group(1))
    return slots


def import_pdf(pdf_path: str, player_name: str) -> dict:
    """Parse a D&D Beyond exported PDF and return the character dict.

    The returned dict has the structure defined in the plan:
    { meta, base, session }
    """
    fields = _get_all_fields(pdf_path)

    class_raw = fields.get("CLASS  LEVEL", "").strip()
    primary_class, primary_level, multiclass_raw = _parse_class_level(class_raw)

    # --- Attributes ---
    attributes = {}
    for attr, score_key, mod_key in _ATTR_FIELDS:
        attributes[attr] = {
            "score":    _int(fields.get(score_key, "0")),
            "modifier": _modifier(fields.get(mod_key, "0")),
        }

    # --- Saving throws ---
    saving_throws = {}
    for attr, prof_key, mod_key in _SAVE_FIELDS:
        saving_throws[attr] = {
            "proficient": _is_proficient(fields.get(prof_key, "")),
            "modifier":   _modifier(fields.get(mod_key, "0")),
        }

    # --- Skills ---
    skills = {}
    for skill, prof_key, val_key, ability_key in _SKILL_FIELDS:
        skills[skill] = {
            "proficient": _is_proficient(fields.get(prof_key, "")),
            "modifier":   _modifier(fields.get(val_key, "0")),
            "ability":    fields.get(ability_key, "").strip() or None,
        }

    hp_max = _int(fields.get("MaxHP", "0"))
    spell_slots_max = _build_spell_slots(fields)

    base = {
        "name":              fields.get("CharacterName", "").strip(),
        "level":             primary_level,
        "class":             _translate_class(primary_class),
        "multiclass":        _translate_class(multiclass_raw) if multiclass_raw else None,
        "race":              _dict_translate(fields.get("RACE", "").strip(), _RACE_PT),
        "background":        _dict_translate(fields.get("BACKGROUND", "").strip(), _BACKGROUND_PT),
        "alignment":         _dict_translate(fields.get("ALIGNMENT", "").strip(), _ALIGNMENT_PT),
        "size":              _dict_translate(fields.get("SIZE", "").strip(), _SIZE_PT),
        "experience_points": fields.get("EXPERIENCE POINTS", "").strip(),
        "hp_max":            hp_max,
        "armor_class":       _int(fields.get("AC", "0")),
        "initiative":        _modifier(fields.get("Init", "0")),
        "speed":             _translate_speed(fields.get("Speed", "").strip()),
        "proficiency_bonus": _modifier(fields.get("ProfBonus", "0")),
        "hit_dice":          fields.get("Total", "").strip(),
        "attributes":        attributes,
        "saving_throws":     saving_throws,
        "skills":            skills,
        "passive_perception":     _int(fields.get("Passive1", "0")),
        "passive_insight":        _int(fields.get("Passive2", "0")),
        "passive_investigation":  _int(fields.get("Passive3", "0")),
        "proficiencies_and_languages": fields.get("ProficienciesLang", "").strip() or None,
        "actions_text":      "\n\n".join(
            v for k in ("Actions1", "Actions2")
            if (v := fields.get(k, "").strip())
        ) or None,
        "features_text":     "\n\n".join(
            v for k in ("FeaturesTraits1", "FeaturesTraits2", "FeaturesTraits3", "FeaturesTraits4")
            if (v := fields.get(k, "").strip())
        ) or None,
        "attacks":           _build_attacks(fields),
        "spell_slots_max":   spell_slots_max,
        "spells":            _build_spells(fields),
        "personality_traits":   fields.get("PersonalityTraits", "").strip() or None,
        "ideals":               fields.get("Ideals", "").strip() or None,
        "bonds":                fields.get("Bonds", "").strip() or None,
        "flaws":                fields.get("Flaws", "").strip() or None,
        "backstory":            fields.get("Backstory", "").strip() or None,
        "allies_organizations": fields.get("AlliesOrganizations", "").strip() or None,
    }

    equipment_base = _build_equipment(fields)
    spell_slots_used = {lvl: 0 for lvl in spell_slots_max}

    session = {
        "hp_current":       hp_max,
        "temp_hp":          0,
        "spell_slots_used": spell_slots_used,
        "currency": {
            "cp": _int(fields.get("CP", "0")),
            "sp": _int(fields.get("SP", "0")),
            "ep": _int(fields.get("EP", "0")),
            "gp": _int(fields.get("GP", "0")),
            "pp": _int(fields.get("PP", "0")),
        },
        "inventory":  equipment_base,
        "notes":      "",
    }

    meta = {
        "player":    player_name,
        "source":    "pdf",
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }

    # --- DeepL: translate free-text fields in one batch ---
    api_key = os.getenv("DEEPL_API_KEY", "").strip()
    if api_key:
        _free_text_keys = [
            "features_text", "actions_text", "proficiencies_and_languages",
            "personality_traits", "ideals", "bonds", "flaws",
            "backstory", "allies_organizations",
        ]
        texts   = [base.get(k) or "" for k in _free_text_keys]
        indices = [i for i, t in enumerate(texts) if t]
        if indices:
            translated = _deepl_translate_batch([texts[i] for i in indices], api_key)
            for pos, i in enumerate(indices):
                base[_free_text_keys[i]] = translated[pos]

        # Translate spell notes in one batch
        spells_with_notes = [(i, s) for i, s in enumerate(base.get("spells", [])) if s.get("notes")]
        if spells_with_notes:
            note_texts = [s["notes"] for _, s in spells_with_notes]
            translated_notes = _deepl_translate_batch(note_texts, api_key)
            for (i, _), translated in zip(spells_with_notes, translated_notes):
                base["spells"][i]["notes"] = translated

        # Translate inventory item names in one batch
        inventory = session.get("inventory", [])
        inv_indices = [i for i, item in enumerate(inventory) if item.get("name")]
        if inv_indices:
            inv_texts = [inventory[i]["name"] for i in inv_indices]
            translated_inv = _deepl_translate_batch(inv_texts, api_key)
            for i, translated in zip(inv_indices, translated_inv):
                session["inventory"][i]["name"] = translated

        # Translate weapon names and notes in one batch
        attacks = base.get("attacks", [])
        atk_to_translate = [(i, "name", a["name"]) for i, a in enumerate(attacks) if a.get("name")]
        atk_to_translate += [(i, "notes", a["notes"]) for i, a in enumerate(attacks) if a.get("notes")]
        if atk_to_translate:
            atk_texts = [t for _, _, t in atk_to_translate]
            translated_atk = _deepl_translate_batch(atk_texts, api_key)
            for (i, field, _), translated in zip(atk_to_translate, translated_atk):
                base["attacks"][i][field] = translated

    return {"meta": meta, "base": base, "session": session}
