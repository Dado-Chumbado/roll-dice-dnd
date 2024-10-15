import pytest
from unittest.mock import AsyncMock, Mock, patch
from plugins.hello_world.plugin_main import PluginMain
from discord.ext import commands


class MockCommand:
    def __init__(self, name, callback):
        self.name = name
        self.callback = callback


@pytest.fixture
def bot():
    # Mock the discord bot
    mock_bot = Mock(spec=commands.Bot)
    mock_bot.commands = {}

    def command(**kwargs):
        def decorator(func):
            cmd = MockCommand(kwargs.get('name', func.__name__), func)
            mock_bot.commands[cmd.name] = cmd
            return cmd

        return decorator

    mock_bot.command = command
    return mock_bot


@pytest.fixture
def plugin(bot):
    # Create an instance of PluginMain
    return PluginMain(bot)


@pytest.fixture
def test_plugin_initialization(bot, plugin):
    # Ensure the plugin was initialized correctly
    assert isinstance(plugin, PluginMain)


@pytest.mark.asyncio
async def test_on_ready_event(bot, plugin):
    # Mock the event and ensure it's called
    events = {}

    def event(func):
        events[func.__name__] = func
        return func

    bot.event = event

    # Simulate the event trigger
    plugin.commands_plugin(bot)

    # Get the on_ready event handler
    assert 'on_ready' in events, "on_ready event should be registered"
    on_ready_handler = events['on_ready']

    # Call the on_ready event handler
    await on_ready_handler()


@pytest.mark.asyncio
async def test_say_hello_world(bot, plugin):
    # Mock context and message sending
    mock_context = AsyncMock()

    # Register the commands
    with patch.object(plugin, 'cm') as mock_cm:
        mock_cm.get_prefix.return_value = "hello"
        mock_cm.get_description.return_value = "Says hello world"
        plugin.commands_plugin(bot)

    # The command should now be in bot.commands
    command_name = "hello"
    assert command_name in bot.commands, f"Command '{command_name}' should exist"

    command = bot.commands[command_name]

    # Call the command and await it
    await command.callback(mock_context)

    # Assert that "Hello World" was sent
    mock_context.send.assert_called_once_with("Hello World")