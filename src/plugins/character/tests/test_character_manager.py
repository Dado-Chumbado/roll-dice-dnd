import json
import math
import pytest
from pathlib import Path
from unittest.mock import patch

from plugins.character.character_manager import (
    update_hp, use_slot, reset_slot, rest, update_inventory,
    load_character, save_character,
)


def _make_char(hp_cur=20, hp_max=27, slots=None):
    return {
        "meta":    {"player": "test", "source": "pdf", "synced_at": "2026-01-01T00:00:00+00:00"},
        "base":    {
            "name": "Trovão", "level": 3, "class": "Barbarian",
            "hp_max": hp_max, "spell_slots_max": slots or {},
        },
        "session": {
            "hp_current": hp_cur, "temp_hp": 0,
            "spell_slots_used": {k: 0 for k in (slots or {})},
            "currency": {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0},
            "inventory": [], "notes": "",
        },
    }


@pytest.fixture
def saved_char(tmp_path):
    """Patch _DATA_DIR and return a factory that saves a character."""
    with patch("plugins.character.character_manager._DATA_DIR", tmp_path):
        def _save(name="test", **kwargs):
            data = _make_char(**kwargs)
            save_character(name, data)
            return name
        yield _save


# HP -----------------------------------------------------------------------


@pytest.fixture
def char_env(tmp_path, monkeypatch):
    import plugins.character.character_manager as cm
    monkeypatch.setattr(cm, "_DATA_DIR", tmp_path)
    return tmp_path


def test_hp_damage(char_env):
    save_character("hero", _make_char(hp_cur=20, hp_max=27))
    data = update_hp("hero", -8)
    assert data["session"]["hp_current"] == 12


def test_hp_heal(char_env):
    save_character("hero", _make_char(hp_cur=10, hp_max=27))
    data = update_hp("hero", 5)
    assert data["session"]["hp_current"] == 15


def test_hp_clamp_min(char_env):
    save_character("hero", _make_char(hp_cur=3, hp_max=27))
    data = update_hp("hero", -99)
    assert data["session"]["hp_current"] == 0


def test_hp_clamp_max(char_env):
    save_character("hero", _make_char(hp_cur=25, hp_max=27))
    data = update_hp("hero", 99)
    assert data["session"]["hp_current"] == 27


def test_hp_not_found(char_env):
    with pytest.raises(FileNotFoundError):
        update_hp("nobody", -5)


# Slots --------------------------------------------------------------------

def test_use_slot(char_env):
    save_character("mage", _make_char(slots={"1": 4, "2": 2}))
    data = use_slot("mage", "1")
    assert data["session"]["spell_slots_used"]["1"] == 1


def test_use_slot_exhausted(char_env):
    char = _make_char(slots={"1": 1})
    char["session"]["spell_slots_used"]["1"] = 1
    save_character("mage", char)
    with pytest.raises(ValueError, match="todos usados"):
        use_slot("mage", "1")


def test_use_slot_invalid_level(char_env):
    save_character("mage", _make_char(slots={"1": 4}))
    with pytest.raises(ValueError):
        use_slot("mage", "9")


def test_reset_slot(char_env):
    char = _make_char(slots={"1": 4})
    char["session"]["spell_slots_used"]["1"] = 3
    save_character("mage", char)
    data = reset_slot("mage", "1")
    assert data["session"]["spell_slots_used"]["1"] == 0


# Rest ---------------------------------------------------------------------

def test_rest_longo_restores_hp(char_env):
    save_character("hero", _make_char(hp_cur=5, hp_max=27))
    data = rest("hero", "longo")
    assert data["session"]["hp_current"] == 27


def test_rest_longo_restores_slots(char_env):
    char = _make_char(hp_cur=5, hp_max=27, slots={"1": 4, "2": 2})
    char["session"]["spell_slots_used"] = {"1": 4, "2": 2}
    save_character("mage", char)
    data = rest("mage", "longo")
    assert data["session"]["spell_slots_used"] == {"1": 0, "2": 0}


def test_rest_curto_recovers_half(char_env):
    save_character("hero", _make_char(hp_cur=0, hp_max=27))
    data = rest("hero", "curto")
    assert data["session"]["hp_current"] == math.ceil(27 / 2)


def test_rest_curto_does_not_exceed_max(char_env):
    save_character("hero", _make_char(hp_cur=26, hp_max=27))
    data = rest("hero", "curto")
    assert data["session"]["hp_current"] == 27


def test_rest_invalid_type(char_env):
    save_character("hero", _make_char())
    with pytest.raises(ValueError):
        rest("hero", "médio")


# Inventory ----------------------------------------------------------------

def test_add_new_item(char_env):
    save_character("hero", _make_char())
    data = update_inventory("hero", "Poção de Cura", 2, add=True)
    assert any(i["name"] == "Poção de Cura" and i["qty"] == 2
               for i in data["session"]["inventory"])


def test_add_existing_item_stacks(char_env):
    char = _make_char()
    char["session"]["inventory"] = [{"name": "Seta", "qty": 10, "weight": None}]
    save_character("hero", char)
    data = update_inventory("hero", "Seta", 5, add=True)
    assert data["session"]["inventory"][0]["qty"] == 15


def test_remove_item(char_env):
    char = _make_char()
    char["session"]["inventory"] = [{"name": "Tocha", "qty": 5, "weight": None}]
    save_character("hero", char)
    data = update_inventory("hero", "Tocha", 3, add=False)
    assert data["session"]["inventory"][0]["qty"] == 2


def test_remove_item_depleted(char_env):
    char = _make_char()
    char["session"]["inventory"] = [{"name": "Tocha", "qty": 2, "weight": None}]
    save_character("hero", char)
    data = update_inventory("hero", "Tocha", 2, add=False)
    assert len(data["session"]["inventory"]) == 0


def test_remove_item_not_found(char_env):
    save_character("hero", _make_char())
    with pytest.raises(ValueError, match="não encontrado"):
        update_inventory("hero", "Espada Vorpal", 1, add=False)


def test_item_name_case_insensitive(char_env):
    char = _make_char()
    char["session"]["inventory"] = [{"name": "Poção de Cura", "qty": 1, "weight": None}]
    save_character("hero", char)
    data = update_inventory("hero", "poção de cura", 1, add=False)
    assert len(data["session"]["inventory"]) == 0
