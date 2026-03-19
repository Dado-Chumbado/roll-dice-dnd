"""Tests for the Telegram bot."""

import os
# Set env vars BEFORE any imports to prevent DB connection
os.environ["save_stats_db"] = ""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

from telegram_bot.bot import (
    TelegramContext,
    is_chat_allowed,
    _handle_roll
)
from telegram_bot.roll_view_telegram import get_roll_text_telegram, generate_dice_text_telegram


class TestTelegramContext:
    """Test the TelegramContext adapter."""

    def test_context_with_username(self):
        """Test context creation with username."""
        # Mock Update with user and chat
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User, id=12345, username="testuser", first_name="Test")
        update.effective_chat = Mock(spec=Chat, id=67890, title="Test Group", username="testgroup")

        ctx = TelegramContext(update)

        assert ctx.author.id == 12345
        assert ctx.author.nick == "testuser"
        assert ctx.channel.name == "Test Group"

    def test_context_without_username(self):
        """Test context creation when user has no username."""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User, id=12345, username=None, first_name="Test")
        update.effective_chat = Mock(spec=Chat, id=67890, title="Test Group", username=None)

        ctx = TelegramContext(update)

        assert ctx.author.id == 12345
        assert ctx.author.nick == "Test"
        assert ctx.channel.name == "Test Group"

    def test_context_fallback_names(self):
        """Test context creation with fallback IDs."""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User, id=12345, username=None, first_name=None)
        update.effective_chat = Mock(spec=Chat, id=67890, title=None, username=None)

        ctx = TelegramContext(update)

        assert ctx.author.id == 12345
        assert ctx.author.nick == "User12345"
        assert ctx.channel.name == "Chat67890"

    @pytest.mark.asyncio
    async def test_send_method(self):
        """Test that send() calls reply_text."""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User, id=12345, username="testuser", first_name="Test")
        update.effective_chat = Mock(spec=Chat, id=67890, title="Test Group", username="testgroup")
        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()

        ctx = TelegramContext(update)
        await ctx.send("Test message")

        update.message.reply_text.assert_called_once_with("Test message")


class TestIsChatAllowed:
    """Test the chat whitelist functionality."""

    def test_empty_whitelist_allows_all(self):
        """Test that empty whitelist allows all chats."""
        with patch.dict(os.environ, {"telegram_allowed_chats": ""}, clear=False):
            update = Mock(spec=Update)
            update.effective_chat = Mock(spec=Chat, id=12345)

            assert is_chat_allowed(update) is True

    def test_whitelist_allows_listed_chat(self):
        """Test that whitelisted chat is allowed."""
        with patch.dict(os.environ, {"telegram_allowed_chats": "12345,67890"}, clear=False):
            update = Mock(spec=Update)
            update.effective_chat = Mock(spec=Chat, id=12345)

            assert is_chat_allowed(update) is True

    def test_whitelist_denies_unlisted_chat(self):
        """Test that non-whitelisted chat is denied."""
        with patch.dict(os.environ, {"telegram_allowed_chats": "12345,67890"}, clear=False):
            update = Mock(spec=Update)
            update.effective_chat = Mock(spec=Chat, id=99999)

            assert is_chat_allowed(update) is False

    def test_whitelist_handles_spaces(self):
        """Test that whitelist handles spaces in config."""
        with patch.dict(os.environ, {"telegram_allowed_chats": "12345 , 67890 "}, clear=False):
            update = Mock(spec=Update)
            update.effective_chat = Mock(spec=Chat, id=67890)

            assert is_chat_allowed(update) is True


class TestTelegramRollView:
    """Test Telegram-specific roll formatting."""

    @pytest.mark.asyncio
    async def test_generate_dice_text_uses_html_bold(self):
        """Test that generate_dice_text_telegram uses HTML formatting for strikethrough."""
        die = Mock()
        die.value = 5
        die.is_active = False
        die.is_critical = False
        die.is_fail = False

        rolled_die = Mock()
        rolled_die.quantity_active = 1
        rolled_die.dice_base = 6
        rolled_die.quantity = 1
        rolled_die.total = 5
        rolled_die.get_list_valid_dice.return_value = [die]

        text, op_desc = await generate_dice_text_telegram([rolled_die], is_sum=True)

        assert "<s>" in text
        assert "</s>" in text
        assert "~~" not in text

    @pytest.mark.asyncio
    async def test_generate_dice_text_critical_uses_sparkles_unicode(self):
        """Test that critical d20 uses unicode sparkles, not Discord shortcode."""
        die = Mock()
        die.value = 20
        die.is_active = True
        die.is_critical = True
        die.is_fail = False

        rolled_die = Mock()
        rolled_die.quantity_active = 1
        rolled_die.dice_base = 20
        rolled_die.quantity = 1
        rolled_die.total = 20
        rolled_die.get_list_valid_dice.return_value = [die]

        text, _ = await generate_dice_text_telegram([rolled_die], is_sum=True)

        assert "✨" in text
        assert ":sparkles:" not in text

    @pytest.mark.asyncio
    async def test_get_roll_text_telegram_uses_html_bold(self):
        """Test that get_roll_text_telegram uses HTML bold tags."""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User, id=1, username="testuser", first_name="Test")
        update.effective_chat = Mock(spec=Chat, id=1, title="Test", username=None)
        ctx = TelegramContext(update)

        die = Mock()
        die.value = 10
        die.is_active = True
        die.is_critical = False
        die.is_fail = False

        rolled_die = Mock()
        rolled_die.quantity_active = 1
        rolled_die.dice_base = 20
        rolled_die.quantity = 1
        rolled_die.total = 10
        rolled_die.get_list_valid_dice.return_value = [die]

        roll = Mock()
        roll.rolled_sum_dice = [rolled_die]
        roll.rolled_subtract_die = []
        roll.additional = ""
        roll.total_roll = 10

        text = await get_roll_text_telegram(ctx, roll, "1d20", "")

        assert "<b>" in text
        assert "</b>" in text
        assert "**" not in text
        # Discord blockquote prefix should not appear
        assert "\n> " not in text


class TestHandleRoll:
    """Test the roll command handler integration."""

    @pytest.mark.asyncio
    async def test_unauthorized_chat(self):
        """Test that unauthorized chats receive rejection message."""
        with patch.dict(os.environ, {"telegram_allowed_chats": "99999"}, clear=False):
            update = Mock(spec=Update)
            update.effective_chat = Mock(spec=Chat, id=12345)
            update.message = Mock(spec=Message)
            update.message.reply_text = AsyncMock()

            context = Mock(spec=ContextTypes.DEFAULT_TYPE)
            context.args = ["2d6"]

            await _handle_roll(update, context)

            update.message.reply_text.assert_called_once_with(
                "This bot is not authorized for this chat."
            )

    @pytest.mark.asyncio
    async def test_default_dice_expression(self):
        """Test that empty args default to d20."""
        with patch.dict(os.environ, {"telegram_allowed_chats": ""}, clear=False):
            with patch("telegram_bot.bot.process_input_dice") as mock_process:
                with patch("telegram_bot.bot.get_roll_text_telegram") as mock_get_text:
                    # Setup mocks
                    mock_roll = Mock()
                    mock_process.return_value = ([mock_roll], "1d20", "")
                    mock_get_text.return_value = "Test result"

                    update = Mock(spec=Update)
                    update.effective_chat = Mock(spec=Chat, id=12345)
                    update.effective_user = Mock(spec=User, id=1, username="test", first_name="Test")
                    update.message = Mock(spec=Message)
                    update.message.reply_text = AsyncMock()

                    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
                    context.args = []

                    await _handle_roll(update, context)

                    # Verify d20 was used
                    assert mock_process.call_args[0][1] == "d20"

    @pytest.mark.asyncio
    async def test_custom_dice_expression(self):
        """Test custom dice expression."""
        with patch.dict(os.environ, {"telegram_allowed_chats": ""}, clear=False):
            with patch("telegram_bot.bot.process_input_dice") as mock_process:
                with patch("telegram_bot.bot.get_roll_text_telegram") as mock_get_text:
                    # Setup mocks
                    mock_roll = Mock()
                    mock_process.return_value = ([mock_roll], "2d6+3", "")
                    mock_get_text.return_value = "Test result"

                    update = Mock(spec=Update)
                    update.effective_chat = Mock(spec=Chat, id=12345)
                    update.effective_user = Mock(spec=User, id=1, username="test", first_name="Test")
                    update.message = Mock(spec=Message)
                    update.message.reply_text = AsyncMock()

                    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
                    context.args = ["2d6+3"]

                    await _handle_roll(update, context)

                    # Verify custom expression was used
                    assert mock_process.call_args[0][1] == "2d6+3"

    @pytest.mark.asyncio
    async def test_advantage_parameter(self):
        """Test that advantage parameter is passed correctly."""
        with patch.dict(os.environ, {"telegram_allowed_chats": ""}, clear=False):
            with patch("telegram_bot.bot.process_input_dice") as mock_process:
                with patch("telegram_bot.bot.get_roll_text_telegram") as mock_get_text:
                    # Setup mocks
                    mock_roll = Mock()
                    mock_process.return_value = ([mock_roll], "1d20", "")
                    mock_get_text.return_value = "Test result"

                    update = Mock(spec=Update)
                    update.effective_chat = Mock(spec=Chat, id=12345)
                    update.effective_user = Mock(spec=User, id=1, username="test", first_name="Test")
                    update.message = Mock(spec=Message)
                    update.message.reply_text = AsyncMock()

                    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
                    context.args = []

                    await _handle_roll(update, context, adv=True)

                    # Verify adv parameter
                    assert mock_process.call_args[1]["adv"] is True
