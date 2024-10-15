import pytest
import os
import json
from unittest.mock import AsyncMock

# Import the classes and functions to be tested
from core.initiative import InitItem, InitTable, InitiativeFile

# Define the root data directory
ROOT_DATA = os.path.join(os.getcwd(), 'data/')

TEST_FOLDER="TESTS"
CHANNEL_NAME="test-channel"

@pytest.fixture
def tmp_path():
    return ROOT_DATA


@pytest.fixture
def init_table(tmp_path):
    """Fixture that creates a temporary initiative file."""
    # Create a temporary file path
    test_file = os.path.join(tmp_path, f'{TEST_FOLDER}.db')

    # Prepare test data
    test_data = [InitItem('Villain', 15, 3, 'Stunned'),
                 InitItem('Hero', 10, 2),
    ]

    init_table = InitTable(test_file)
    init_table.initiative_file.save_initiative_table(CHANNEL_NAME, test_data)

    # load again the init Table
    init_table = InitTable(test_file)

    # Force load data
    init_table.load_init_table(CHANNEL_NAME)

    yield init_table  # Provide the path to the test file


def test_load_initiative_table(init_table):

    assert len(init_table.initiative_table) == 2
    assert init_table.initiative_table[1].name == 'Hero'
    assert init_table.initiative_table[0].condition == 'Stunned'


# Test saving initiative table
def test_save_initiative_table(init_table):
    # Create a sample list of InitItem objects
    test_data = [InitItem('Alice', 10, 2),
                 InitItem('John', 15, 3, 'Stunned')
                 ]
    init_table.initiative_file.save_initiative_table(CHANNEL_NAME, test_data)

    # Check if the file was created and contains the correct data
    file_name = init_table.initiative_file.get_filename(CHANNEL_NAME)
    with open(file_name, 'r') as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["condition"] == "Stunned"


@pytest.mark.asyncio
async def test_add_initiative(init_table):
    await init_table.add(CHANNEL_NAME, "Charlie", 10, "1")
    assert len(init_table.initiative_table) == 3  # Considering that the table is loaded
    assert init_table.initiative_table[2].name == "Charlie"
    assert init_table.initiative_table[2].total == 11

    await init_table.add(CHANNEL_NAME, "Bobby", 2, "5")
    assert len(init_table.initiative_table) == 4
    assert init_table.initiative_table[3].name == "Bobby"
    assert init_table.initiative_table[3].total == 7

    await init_table.add(CHANNEL_NAME, "Anna", 18, "5")
    assert len(init_table.initiative_table) == 5
    # Check auto sort
    assert init_table.initiative_table[4].name == "Bobby"
    assert init_table.initiative_table[0].name == "Anna"
    assert init_table.initiative_table[0].total == 23


@pytest.mark.asyncio
async def test_reset_initiative(init_table):
    await init_table.reset(CHANNEL_NAME)
    assert len(init_table.initiative_table) == 0
    assert init_table.current == 1


@pytest.mark.asyncio
async def test_add_condition(init_table):
    await init_table.add_condition(CHANNEL_NAME, 1, "Paralyzed")
    assert init_table.initiative_table[0].condition == "Paralyzed"


@pytest.mark.asyncio
async def test_remove_condition(init_table):
    await init_table.remove_condition(CHANNEL_NAME, 2)
    assert init_table.initiative_table[1].condition == ""


@pytest.mark.asyncio
async def test_remove_index(init_table):

    assert len(init_table.initiative_table) == 2
    await init_table.remove_index(CHANNEL_NAME, 1) # Index starting with 1 (based on UI)
    assert len(init_table.initiative_table) == 1
    assert init_table.initiative_table[0].name == "Hero"
    await init_table.remove_index(CHANNEL_NAME, 1)
    assert len(init_table.initiative_table) == 0


@pytest.mark.asyncio
async def test_next_previous(init_table):
    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Hero"

    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Villain"

    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Hero"

    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Villain"

    result = await init_table.previous(CHANNEL_NAME)
    assert result.name == "Hero"


@pytest.mark.asyncio
async def test_next_previous_changes(init_table):
    assert init_table.current == 1

    await init_table.add(CHANNEL_NAME, "Anna", 18, "5")
    assert len(init_table.initiative_table) == 3
    assert init_table.initiative_table[0].name == "Anna"

    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Villain" # Next is villain because ANNA is the first now
    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Hero"
    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Anna"  # Start over
    assert init_table.current == 1

    await init_table.remove_index(CHANNEL_NAME, 1) # remove Villain
    assert init_table.current == 1
    assert len(init_table.initiative_table) == 2

    # Current now should be Anna
    assert init_table.current == 1
    result = await init_table.next(CHANNEL_NAME)
    assert result.name == "Hero"


@pytest.mark.asyncio
async def test_next_previous_changes_2(init_table):
    assert init_table.current == 1
    await init_table.remove_index(CHANNEL_NAME, 1)  # remove Villain
    await init_table.add(CHANNEL_NAME, "Anna", 18, "5")
    await init_table.add(CHANNEL_NAME, "Dragon", 14, "2")
    await init_table.add(CHANNEL_NAME, "Healer", 12, "1")
    result = await init_table.previous(CHANNEL_NAME)
    assert result.name == "Hero"  # since current was 1, go back to the last one

@pytest.mark.asyncio
async def test_show_initiative_table(init_table):
    context = AsyncMock()  # Mocking discord context for sending messages
    await init_table.show(CHANNEL_NAME, context)
    context.send.assert_called_once()
    message = context.send.call_args[0][0]
    assert "Hero" in message
    assert "Villain" in message
    assert "15    + 3   18" in message
    assert "10    + 2   12" in message
    assert "Stunned" in message

@pytest.mark.asyncio
async def test_show_initiative_table_adding(init_table):
    await init_table.add(CHANNEL_NAME, "Anna", 18, "5")
    await init_table.add(CHANNEL_NAME, "Dragon", 14, "2")

    context = AsyncMock()  # Mocking discord context for sending messages

    await init_table.show(CHANNEL_NAME, context)
    context.send.assert_called_once()
    message = context.send.call_args[0][0]
    assert "> 1" in message

    context = AsyncMock()
    await init_table.next(CHANNEL_NAME)
    await init_table.show(CHANNEL_NAME, context)

    context.send.assert_called_once()
    message = context.send.call_args[0][0]

    assert "> 2" in message
    context = AsyncMock()
    await init_table.next(CHANNEL_NAME)
    await init_table.show(CHANNEL_NAME, context)

    context.send.assert_called_once()
    message = context.send.call_args[0][0]
    assert "> 3" in message

    context = AsyncMock()
    await init_table.next(CHANNEL_NAME)
    await init_table.show(CHANNEL_NAME, context)
    context.send.assert_called_once()
    message = context.send.call_args[0][0]
    assert "> 4" in message

    context = AsyncMock()
    await init_table.next(CHANNEL_NAME)
    await init_table.show(CHANNEL_NAME, context)

    context.send.assert_called_once()
    message = context.send.call_args[0][0]
    assert "> 1" in message

