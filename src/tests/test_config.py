"""Tests for ConfigManager, especially the platform-aware get_prefix."""

import json

import pytest

from config import ConfigManager


@pytest.fixture
def config_manager(tmp_path):
    config_data = {
        "roll": {
            "advantage": {"alias": "v", "description": "Roll with advantage"},
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data))
    return ConfigManager(str(config_path))


def test_get_prefix_defaults_to_discord_platform(config_manager, monkeypatch):
    monkeypatch.delenv("DISCORD_CMD_ROLL_ADVANTAGE", raising=False)
    monkeypatch.delenv("TELEGRAM_CMD_ROLL_ADVANTAGE", raising=False)

    assert config_manager.get_prefix("roll", "advantage") == "v"


def test_get_prefix_discord_env_override_still_works(config_manager, monkeypatch):
    monkeypatch.setenv("DISCORD_CMD_ROLL_ADVANTAGE", "vantagem")

    assert config_manager.get_prefix("roll", "advantage") == "vantagem"


def test_get_prefix_telegram_platform_falls_back_to_same_config_alias(config_manager, monkeypatch):
    monkeypatch.delenv("TELEGRAM_CMD_ROLL_ADVANTAGE", raising=False)

    assert config_manager.get_prefix("roll", "advantage", platform="telegram") == "v"


def test_get_prefix_telegram_env_override_is_independent_of_discord(config_manager, monkeypatch):
    monkeypatch.setenv("TELEGRAM_CMD_ROLL_ADVANTAGE", "adv")
    monkeypatch.delenv("DISCORD_CMD_ROLL_ADVANTAGE", raising=False)

    assert config_manager.get_prefix("roll", "advantage", platform="telegram") == "adv"
    assert config_manager.get_prefix("roll", "advantage") == "v"
