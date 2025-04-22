import pytest
from core.dice_engine import process_input_dice
from core.helper import send_message
from core.roll_view import get_roll_text, generate_dice_text
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_long_dice_text():
    dice_data = "100d6"
    rolls, dice_data_result, reroll = await process_input_dice(None, dice_data)

    context = AsyncMock()  # Mocking discord context for sending messages

    response = await get_roll_text(context, rolls[0], dice_data, reroll,
                                   extra_info="", skip_resume=False,
                                   skip_user_and_dice=False)
    assert "100d6 => [" in response
    assert len(response) < 2000



@pytest.mark.asyncio
async def test_roll_text_view():
    dice_data = "2d6+3d8-1d4"
    rolls, dice_data, reroll = await process_input_dice(None, dice_data)

    context = AsyncMock()  # Mocking discord context for sending messages

    response = await get_roll_text(context, rolls[0], dice_data, reroll,
                         extra_info="", skip_resume=False, skip_user_and_dice=False)
    assert "2d6 => [" in response
    assert "3d8 => [" in response
    assert "1d4 => [" in response

@pytest.mark.asyncio
async def test_roll_text_view_2():
    dice_data = "4d6+4d6+4d6"
    rolls, dice_data, reroll = await process_input_dice(None, dice_data)

    context = AsyncMock()  # Mocking discord context for sending messages

    response = await get_roll_text(context, rolls[0], dice_data, reroll,
                         extra_info="", skip_resume=False, skip_user_and_dice=False)
    assert "4d6 => [" in response
    assert "4d6 => [" in response
    assert "4d6 => [" in response

@pytest.mark.asyncio
async def test_roll_text_view_2():
    dice_data = "d8+5-1"
    rolls, dice_data, reroll = await process_input_dice(None, dice_data)

    context = AsyncMock()  # Mocking discord context for sending messages

    response = await get_roll_text(context, rolls[0], dice_data, reroll,
                         extra_info="", skip_resume=False, skip_user_and_dice=False)
    assert "1d8 => [" in response
    assert "5 - 1 = " in response

@pytest.mark.asyncio
async def test_roll_text_big_text(monkeypatch):
    # set limit to test env limit_of_dice_per_roll and limit_of_dice_size
    monkeypatch.setenv("limit_of_dice_per_roll", '1000')
    monkeypatch.setenv("limit_of_die_size", '1000')

    dice_data = "666d6"
    rolls, dice_data, reroll = await process_input_dice(None, dice_data)

    context = AsyncMock()  # Mocking discord context for sending messages

    response = await get_roll_text(context, rolls[0], dice_data, reroll,
                         extra_info="", skip_resume=False, skip_user_and_dice=False)
    assert len(response) > 2000
    await send_message(context, response)
    context.send.assert_called()
    message = context.send.call_args[0][0]
    assert len(message) <= 2000
