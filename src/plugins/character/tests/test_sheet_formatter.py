import pytest
from plugins.character.sheet_formatter import format_sheet, format_sheet_simple, format_sheet_full, _hp_bar, _sign


def _minimal_char(hp_cur=20, hp_max=27):
    return {
        "meta":    {"player": "test", "source": "pdf", "synced_at": "2026-01-01T00:00:00+00:00"},
        "base":    {
            "name": "Trovão", "level": 3, "class": "Barbarian", "multiclass": None,
            "race": "Goliath", "background": "Custom", "alignment": "CN",
            "size": "Medium", "experience_points": "",
            "hp_max": hp_max, "armor_class": 19, "initiative": 2,
            "speed": "35 ft.", "proficiency_bonus": 2, "hit_dice": "3d12",
            "attributes": {a: {"score": 10, "modifier": 0} for a in
                           ["strength","dexterity","constitution","intelligence","wisdom","charisma"]},
            "saving_throws": {a: {"proficient": False, "modifier": 0} for a in
                              ["strength","dexterity","constitution","intelligence","wisdom","charisma"]},
            "skills": {},
            "passive_perception": 10, "passive_insight": 10, "passive_investigation": 10,
            "proficiencies_and_languages": None, "actions_text": None, "features_text": None,
            "attacks": [], "spell_slots_max": {}, "spells": [],
            "personality_traits": None, "ideals": None, "bonds": None, "flaws": None,
            "backstory": None, "allies_organizations": None,
        },
        "session": {
            "hp_current": hp_cur, "temp_hp": 0, "spell_slots_used": {},
            "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
            "inventory": [], "notes": "",
        },
    }


def test_format_sheet_simple_contains_name():
    assert "Trovão" in format_sheet_simple(_minimal_char())


def test_format_sheet_full_contains_name():
    assert "Trovão" in format_sheet_full(_minimal_char())


def test_format_sheet_dispatcher_simples():
    assert "Trovão" in format_sheet(_minimal_char(), mode="simples")


def test_format_sheet_dispatcher_completa():
    assert "Atributos" in format_sheet(_minimal_char(), mode="completa")


def test_format_sheet_hp():
    sheet = format_sheet_simple(_minimal_char(hp_cur=15, hp_max=27))
    assert "15/27" in sheet


def test_format_sheet_full_hp_bar():
    sheet = format_sheet_simple(_minimal_char(hp_cur=27, hp_max=27))
    assert "██████████" in sheet


def test_format_sheet_empty_hp_bar():
    sheet = format_sheet_simple(_minimal_char(hp_cur=0, hp_max=27))
    assert "░░░░░░░░░░" in sheet


def test_hp_bar_full():
    assert _hp_bar(10, 10) == "[██████████]"


def test_hp_bar_empty():
    assert _hp_bar(0, 10) == "[░░░░░░░░░░]"


def test_hp_bar_half():
    bar = _hp_bar(5, 10)
    assert bar == "[█████░░░░░]"


def test_sign_positive():
    assert _sign(4) == "+4"


def test_sign_negative():
    assert _sign(-1) == "-1"


def test_sign_zero():
    assert _sign(0) == "+0"


def test_spell_slots_shown_full():
    char = _minimal_char()
    char["base"]["spell_slots_max"] = {"1": 4, "2": 2}
    char["session"]["spell_slots_used"] = {"1": 1, "2": 0}
    sheet = format_sheet_full(char)
    assert "Espaços de Magia" in sheet
    assert "Nível 1" in sheet


def test_spell_slots_shown_simple():
    char = _minimal_char()
    char["base"]["spell_slots_max"] = {"1": 4, "2": 2}
    char["session"]["spell_slots_used"] = {"1": 1, "2": 0}
    sheet = format_sheet_simple(char)
    assert "Nv1" in sheet


def test_attacks_shown():
    char = _minimal_char()
    char["base"]["attacks"] = [{"name": "Greataxe", "bonus": "+6", "damage": "1d12+4 Slashing", "notes": None}]
    assert "Greataxe" in format_sheet_simple(char)
    assert "Greataxe" in format_sheet_full(char)
