# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord bot for rolling dice and managing initiative tables for tabletop RPG games (primarily D&D). The bot is built with discord.py and uses Poetry for dependency management.

## Development Commands

### Setup and Running
- **Install dependencies**: `poetry install`
- **Activate virtual environment**: `poetry shell`
- **Run the Discord bot**: `poetry run python src/main.py`
- **Run the Telegram bot**: `poetry run python src/telegram_bot/main.py`
- **Run both bots via Docker**: `docker-compose up`

### Testing
- **Run all tests**: `poetry run pytest`
- **Run specific test file**: `poetry run pytest src/tests/test_dice_engine.py`
- **Run with verbose output**: `poetry run pytest -v`

Note: pytest.ini sets `pythonpath = src` so imports work correctly in tests.

### Environment Setup
- Copy `src/.env.example` to `src/.env` and configure tokens
- Copy `src/config.json.example` to `src/config.json` for command configuration
- Environment variables in `src/.env`:
  - `discord_token` — Discord bot token
  - `telegram_token` — Telegram bot token
  - `telegram_allowed_chats` — Comma-separated chat IDs to whitelist (empty = allow all)
  - `command_char` (default: `!`) — Discord command prefix
  - `limit_of_dice_per_roll` (default: 100)
  - `limit_of_die_size` (default: 100)
  - `save_stats_db` (set to "True" or "1" to enable stats tracking)
  - `sentry_dsn` (optional, for error tracking)
  - Database: `db`, `user`, `pass`, `host`, `port` (PostgreSQL, required when `save_stats_db` is enabled)
  - D20 IRL integration: `D20_IRL_ENABLED`, `D20_IRL_URL`, `D20_IRL_USERNAME`, `D20_IRL_TOKEN`, `D20_IRL_COMMAND`
  - Telegram command overrides: `TELEGRAM_CMD_ROLL`, `TELEGRAM_CMD_ADV`, `TELEGRAM_CMD_DIS`

## Architecture

### Core Components

**src/main.py** - Entry point that:
- Loads environment and config
- Sets up Discord bot with intents
- Initializes database via `db.models.setup_db()`
- Registers commands via `commands_setup()`
- Starts the bot

**src/commands/** - Discord command handlers organized by feature:
- `roll_dice.py` - All dice rolling commands (standard, advantage, disadvantage, critical, DM rolls)
- `initiative.py` - Initiative table management commands
- `stats.py` - Player and session statistics commands
- `debug.py` - Utility commands (ping, help)

**src/core/** - Business logic layer:
- `dice_engine.py` - Parses dice expressions, handles validation, processes rolls
- `roll.py` - Core data models: `Dice`, `RolledDice`, `Roll`. Implements advantage/disadvantage/critical logic
- `roll_view.py` - Formats roll results for Discord display
- `initiative.py` - Initiative table management with file-based persistence to `data/`
- `stats_db.py` - Database operations for statistics tracking
- `dm_manager.py` - DM assignment per channel, persisted to `data/dm_settings.json`. Exposes a global `dm_manager` singleton
- `helper.py` - Shared utility functions

**src/telegram_bot/** - Telegram bot (shares `src/core/` with Discord bot):
- `main.py` - Entry point; loads `.env` and starts polling
- `bot.py` - Command handlers and `TelegramContext` adapter
- `roll_view_telegram.py` - HTML-formatted roll output for Telegram
- `d20_irl_client.py` - HTTP client for the Raspberry Pi physical dice API

**src/db/** - Database layer:
- `models.py` - Peewee ORM models (`PlayerStats`, `RollDb`) for PostgreSQL via Peewee

**src/config.py** - ConfigManager that loads command aliases and descriptions from config.json

**src/plugin_manager.py** - Dynamic plugin loading system

### Key Data Flow

1. **Dice Rolling**:
   - User command → `commands/roll_dice.py` → `process_input_dice()` → `parse_dice()` / `parse_additional()` → `calculate_dice()` → `generate_dice_roll()` → `Roll` object → `get_roll_text()` → Discord message

2. **Initiative**:
   - Commands in `commands/initiative.py` use singleton `InitTable` instance
   - Rolls processed via `dice_engine.process_input_dice()`
   - Results stored in `InitTable` and persisted to JSON files in `data/` directory

3. **Advantage/Disadvantage Logic**:
   - Implemented in `RolledDice.set_advantage()` in `core/roll.py`
   - Marks non-selected dice as inactive using `is_active` flag
   - Advantage: keeps highest roll, disadvantage: keeps lowest

4. **Telegram/Discord shared core**:
   - `TelegramContext` in `telegram_bot/bot.py` is an adapter that wraps a Telegram `Update` to expose `.author.id`, `.author.nick`, `.channel.name`, and `async send()` — the same interface Discord's `context` provides
   - All core dice logic (`process_input_dice`, etc.) is platform-agnostic and works with either context

### Plugin System

Plugins live in `src/plugins/`. Each plugin:
- Must have a file starting with `plugin_` (e.g., `plugin_magic.py`)
- Must contain a class following naming pattern `Plugin{ModuleName}` (e.g., `PluginMagic`)
- Must inherit from `Plugin` base class
- Must implement `commands_plugin(self, bot)` method
- Can include `plugin_config.json` for command configuration
- Should include tests in `tests/` subdirectory

Plugins are auto-discovered and loaded by `plugin_manager.load_plugins()`.

**Character sheet plugin** (`src/plugins/character/`) — imports D&D Beyond PDFs and manages session state:
- `pdf_extractor.py` — reads Widget annotations from PDF via `pypdf`; field mapping documented inside
- `character_manager.py` — load/save JSON, `update_hp`, `use_slot`, `reset_slot`, `rest`, `update_inventory`
- `sheet_formatter.py` — Discord formatting; `format_sheet(data, mode="simples"|"completa")`
- `plugin_character.py` — Discord commands: `!importar`, `!ficha`, `!hp`, `!slot`, `!slots`, `!descanso`, `!inventario`, `!item`
- `src/telegram_bot/character_telegram.py` — Telegram handlers for the same commands (`/ficha`, `/hp`, etc.)
- `src/telegram_bot/sheet_formatter_telegram.py` — HTML formatting for Telegram

Character JSON files stored in `data/characters/<nome>.json`. In Docker, volume-mounted at `/var/lib/roll-dice-dnd` → persists across rebuilds.

### Configuration System

Commands are configured in `src/config.json`:
```json
{
  "roll": {
    "roll_dice": {"alias": "r", "description": "..."},
    "advantage": {"alias": "v", "description": "..."}
  }
}
```

ConfigManager provides `get_prefix(category, command)` and `get_description(category, command)` methods.

## Important Patterns

### Dice Expression Parsing
- The system uses regex patterns to parse expressions like `2d6+1d20-3d8+5`
- `parse_dice()` extracts all dice rolls (positive and negative)
- `parse_additional()` removes dice expressions and returns remaining modifiers
- `fix_dice_expression()` normalizes input (e.g., "5" becomes "1d20+5")
- Limits are enforced from environment variables

### Advantage/Disadvantage Implementation
- Both use `adv` parameter (True = advantage, False = disadvantage)
- Dice engine automatically converts d20 to 2d20 for advantage/disadvantage
- `double_adv` parameter converts to 3d20
- `RolledDice.set_advantage()` determines which dice to mark inactive
- Inactive dice are shown with strikethrough formatting in output

### Critical Damage
- Doubles the number of dice in `process_input_dice()` when `critical=True`
- First half of dice are maximized in `RolledDice.apply_critical()`

### Reroll Mechanics
- Dice expressions can end with `r1`, `r2`, etc. to reroll values ≤ threshold
- Original rolls marked inactive, new rolls added to results
- Implemented in `RolledDice.apply_reroll()`

### Stats Tracking
- Asynchronous task created for each roll when `save_stats_db` is enabled
- Uses Peewee ORM with PostgreSQL backend
- Tracks: player_id, channel, die type, value, critical/fail status

## Testing Approach

- Tests use pytest with pytest-asyncio for async support
- `conftest.py` provides shared fixtures
- Mock Discord context objects for command testing
- Test files mirror source structure (e.g., `test_dice_engine.py` tests `dice_engine.py`)

## Common Tasks

### Adding a new dice roll command
1. Add command configuration to `src/config.json`
2. Create hybrid_command in `src/commands/roll_dice.py`
3. Call `process_input_dice()` with appropriate parameters (adv, critical, etc.)
4. Send formatted output using `get_roll_text()`

### Adding a new initiative command
1. Add command configuration to `src/config.json`
2. Add command handler in `src/commands/initiative.py`
3. Use the shared `init_items` (InitTable instance)
4. Remember to delete and recreate `initiative_last_msg` for table updates

### Creating a new plugin
1. Create folder in `src/plugins/` with your plugin name
2. Create `plugin_{name}.py` with class `Plugin{Name}(Plugin)`
3. Implement `commands_plugin(self, bot)` method
4. Optionally add `plugin_config.json` for command configuration
5. Add tests in `tests/` subdirectory
6. Plugin will be auto-loaded on bot startup
