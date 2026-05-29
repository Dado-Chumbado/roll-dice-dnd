import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.stats_db import show_player_stats, show_session_stats, normalize_dice_type


@patch('core.stats_db.get_display_name', return_value="Player1")
@patch('core.stats_db.connect_db')
@patch('core.stats_db.RollDb.select')
@pytest.mark.asyncio
async def test_show_player_stats(mock_select, mock_connect_db, mock_display_name):
    mock_connect_db.return_value.__enter__ = MagicMock(return_value=None)
    mock_connect_db.return_value.__exit__ = MagicMock(return_value=False)

    def _roll(dice, value, critical=False, fail=False):
        r = MagicMock()
        r.dice = dice
        r.value = value
        r.critical = critical
        r.fail = fail
        return r

    rolls = [
        _roll("d20", 20, critical=True),
        _roll("d20", 1, fail=True),
        _roll("d20", 15),
        _roll("d6", 4),
        _roll("d6", 6),
    ]
    mock_select.return_value.where.return_value = rolls

    mock_context = AsyncMock()
    mock_context.author.id = 1
    mock_context.channel.name = "general"
    await show_player_stats(mock_context, "general")

    sent = mock_context.send.call_args[0][0]
    assert "🎲 Stats for Player1" in sent
    assert "Total rolls: 5" in sent
    assert "Total rolled value: 46" in sent
    assert "Average per roll: 9.20" in sent
    assert "Critical hits (d20 only): 1" in sent
    assert "Failures (d20 only): 1" in sent
    assert "D20: 3 rolls, sum 36, avg 12.00" in sent
    assert "D6: 2 rolls, sum 10, avg 5.00" in sent


mock_data = MagicMock()
mock_data.data = {
    'critical_hits': 10,
    'failures': 2,
    'top_critics': 3,
    'top_failures': 2,
    'total_rolled': 123,
    'd20s_by_player': []
}


# @patch('core.stats_db.get_session_stats')
# @patch('core.stats_db.get_display_name')
# @pytest.mark.asyncio
# async def test_show_session_stats(get_display_name, get_session_stats):
#     get_session_stats.return_value = mock_data  # Example mock return value
#     get_display_name.return_value = "PlayerTest"
#
#     # Arrange
#     mock_ctx = AsyncMock()
#     channel = "General"
#     date = "2024-09-01"
#
#     # Act
#     await show_session_stats(mock_ctx, channel, date)
#
#     # Assert
#     mock_ctx.send.assert_called_once_with(
#         "```STATISTICS General from 2024-09-01\n"
#         "Total critical hits: 10\nTotal failures: 5\n"
#         "Critical/failure ratio: 2.00\n"
#         "Player with the most critical hits: Luck Guy with 4 critical hits!\n"
#         "Player with the most failures:  Player Unluck with 8 failures!\n"
#         "Luckiest player: Luck Guy with 6.76% critical hits\n"
#         "Unluckiest player: Player Unlucky with 6.25% failures\n"
#         "Total rolled: 100```"
#     )


# --- normalize_dice_type tests ---

def test_normalize_dice_type_none():
    assert normalize_dice_type(None) is None

def test_normalize_dice_type_valid_with_prefix():
    assert normalize_dice_type("d20") == "d20"
    assert normalize_dice_type("D6") == "d6"
    assert normalize_dice_type("d100") == "d100"

def test_normalize_dice_type_valid_number_only():
    assert normalize_dice_type("20") == "d20"
    assert normalize_dice_type("6") == "d6"

def test_normalize_dice_type_invalid():
    with pytest.raises(ValueError, match="Unknown dice type"):
        normalize_dice_type("d99")
    with pytest.raises(ValueError, match="Unknown dice type"):
        normalize_dice_type("d3")


# --- _parse_first_arg tests ---

from commands.stats import _parse_first_arg

def test_parse_first_arg_none():
    assert _parse_first_arg(None) == (None, None)

def test_parse_first_arg_valid_dice():
    assert _parse_first_arg("d20") == ("d20", None)
    assert _parse_first_arg("D6") == ("d6", None)
    assert _parse_first_arg("20") == ("d20", None)

def test_parse_first_arg_channel_name():
    assert _parse_first_arg("general") == (None, "general")
    assert _parse_first_arg("my-channel") == (None, "my-channel")

def test_parse_first_arg_invalid_die_raises():
    with pytest.raises(ValueError, match="Unknown dice type"):
        _parse_first_arg("d99")


# --- show_player_stats with dice_type filter ---

def _make_roll(dice, value, critical=False, fail=False):
    r = MagicMock()
    r.dice = dice
    r.value = value
    r.critical = critical
    r.fail = fail
    return r


@patch('core.stats_db.get_display_name', return_value="Player1")
@patch('core.stats_db.connect_db')
@patch('core.stats_db.RollDb.select')
@pytest.mark.asyncio
async def test_show_player_stats_filtered_d20(mock_select, mock_connect_db, mock_display_name):
    mock_connect_db.return_value.__enter__ = MagicMock(return_value=None)
    mock_connect_db.return_value.__exit__ = MagicMock(return_value=False)

    rolls = [
        _make_roll("d20", 20, critical=True),
        _make_roll("d20", 1, fail=True),
        _make_roll("d20", 15),
    ]
    mock_select.return_value.where.return_value.where.return_value = rolls

    ctx = AsyncMock()
    ctx.author.id = 1
    await show_player_stats(ctx, "general", dice_type="d20")

    sent = ctx.send.call_args[0][0]
    assert "[D20 only]" in sent
    assert "Critical hits" in sent
    assert "Failures" in sent


@patch('core.stats_db.get_display_name', return_value="Player1")
@patch('core.stats_db.connect_db')
@patch('core.stats_db.RollDb.select')
@pytest.mark.asyncio
async def test_show_player_stats_filtered_d6_no_d20_lines(mock_select, mock_connect_db, mock_display_name):
    mock_connect_db.return_value.__enter__ = MagicMock(return_value=None)
    mock_connect_db.return_value.__exit__ = MagicMock(return_value=False)

    rolls = [_make_roll("d6", 4), _make_roll("d6", 6), _make_roll("d6", 2)]
    mock_select.return_value.where.return_value.where.return_value = rolls

    ctx = AsyncMock()
    ctx.author.id = 1
    await show_player_stats(ctx, "general", dice_type="d6")

    sent = ctx.send.call_args[0][0]
    assert "[D6 only]" in sent
    assert "Critical hits" not in sent
    assert "Failures" not in sent