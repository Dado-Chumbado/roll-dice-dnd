import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.stats_db import show_player_stats, show_session_stats


# Mock the player stats response
mock_ps = MagicMock()
mock_ps.total_dice_rolled = 100
mock_ps.total_d20_rolled = 5
mock_ps.total_d20_critical_rolled = 2
mock_ps.total_d20_fails_rolled = 1
mock_ps.total_d20_values_rolled = 32

mock_ps.total_d4_values_rolled = 10
mock_ps.total_d4_rolled = 8

mock_ps.total_d6_values_rolled = 20
mock_ps.total_d6_rolled = 86

mock_ps.total_d8_values_rolled = 6
mock_ps.total_d8_rolled = 24

mock_ps.total_d10_values_rolled = 40
mock_ps.total_d10_rolled = 16

mock_ps.total_d12_values_rolled = 32
mock_ps.total_d12_rolled = 43

mock_ps.total_d100_values_rolled = 25
mock_ps.total_d100_rolled = 142

mock_ps.sum_dice_number_rolled = 200


@patch('core.stats_db.PlayerStats.get', create=True)
@pytest.mark.asyncio
async def test_show_player_stats(player_get):
    # Return the mocked player-stats object used to build the message
    player_get.return_value = mock_ps

    mock_context = AsyncMock()
    mock_context.author.id = 1
    mock_context.author.display_name = "Player1"
    mock_context.channel.name = "General"
    await show_player_stats(mock_context, mock_context.channel.name)

    # Assert
    mock_context.send.assert_called_once_with(
        "```You have rolled a total of 100 dice! \nD20 rolled 5 times! with "
        "2 critical hits and 1 failures.\nThe sum of your d20's is 32.\n"
        "Total of other dice:\n D20 rolled 5 times. The sum is 32 \n D4 rolled"
        " 8 times. The sum is 10 \n D6 rolled 86 times. The sum is 20 \n D8 "
        "rolled 24 times. The sum is 6 \n D10 rolled 16 times. The sum is 40"
        " \n D12 rolled 43 times. The sum is 32 \n D100 rolled 142 times. "
        "The sum is 25 \nTotal critical hits for D20: 2\nTotal failures for "
        "D20: 1\nThe total of all rolled dice is: 200```"
    )


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