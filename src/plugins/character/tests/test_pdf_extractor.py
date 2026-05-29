import pytest
from plugins.character.pdf_extractor import (
    _parse_class_level,
    _modifier,
    _is_proficient,
    _int,
)


def test_parse_class_level_simple():
    cls, lvl, mc = _parse_class_level("Barbarian 3")
    assert cls == "Barbarian"
    assert lvl == 3
    assert mc is None


def test_parse_class_level_multiclass():
    cls, lvl, mc = _parse_class_level("Fighter 5/Wizard 3")
    assert cls == "Fighter"
    assert lvl == 5
    assert mc == "Fighter 5/Wizard 3"


def test_parse_class_level_spaces():
    cls, lvl, mc = _parse_class_level("  Rogue 8  ")
    assert cls == "Rogue"
    assert lvl == 8


def test_modifier_positive():
    assert _modifier("+4") == 4


def test_modifier_negative():
    assert _modifier("-1") == -1


def test_modifier_zero():
    assert _modifier("0") == 0


def test_modifier_empty():
    assert _modifier("") == 0


def test_is_proficient_bullet():
    assert _is_proficient("•") is True


def test_is_proficient_p():
    assert _is_proficient("P") is True


def test_is_proficient_empty():
    assert _is_proficient("") is False


def test_int_valid():
    assert _int("27") == 27


def test_int_invalid():
    assert _int("--") == 0


def test_int_default():
    assert _int("", default=5) == 5
