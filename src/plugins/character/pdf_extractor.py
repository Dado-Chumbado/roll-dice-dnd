import re
from datetime import datetime, timezone
import pypdf

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
            "damage": fields.get(dmg_key, "").strip() or None,
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
            "cast_time":  fields.get(f"spellCastingTime{i}", "").strip() or None,
            "range":      fields.get(f"spellRange{i}", "").strip() or None,
            "components": fields.get(f"spellComponents{i}", "").strip() or None,
            "duration":   fields.get(f"spellDuration{i}", "").strip() or None,
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
            "cast_time":  fields.get(f"CastingTime{i}", "").strip() or None,
            "range":      fields.get(f"Range{i}", "").strip() or None,
            "components": fields.get(f"Components{i}", "").strip() or None,
            "duration":   fields.get(f"Duration{i}", "").strip() or None,
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
        "class":             primary_class,
        "multiclass":        multiclass_raw,
        "race":              fields.get("RACE", "").strip(),
        "background":        fields.get("BACKGROUND", "").strip(),
        "alignment":         fields.get("ALIGNMENT", "").strip(),
        "size":              fields.get("SIZE", "").strip(),
        "experience_points": fields.get("EXPERIENCE POINTS", "").strip(),
        "hp_max":            hp_max,
        "armor_class":       _int(fields.get("AC", "0")),
        "initiative":        _modifier(fields.get("Init", "0")),
        "speed":             fields.get("Speed", "").strip(),
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

    return {"meta": meta, "base": base, "session": session}
