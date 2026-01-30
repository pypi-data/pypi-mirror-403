# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ai-comm is a cross-AI CLI communication tool for Kitty terminal. It enables AI assistants (Claude Code, Codex CLI, Gemini CLI, Aider, Cursor, OpenCode) running in separate Kitty windows to communicate with each other programmatically.

## Commands

```bash
# Install dependencies
uv sync

# Run CLI
uv run ai-comm --help
uv run ai-comm list-ai-windows
uv run ai-comm send "message" -w <window_id>

# Lint and type check
uv run ruff check src/
uv run ruff check --fix src/
uv run mypy src/

# Format code
uv run ruff format src/

# Run inline Python code
echo "from ai_comm import __version__; print(__version__)" | uv run -
```

**Note:** `uv` cannot be sandboxed due to system configuration access. Always run `uv` commands with `dangerouslyDisableSandbox: true`.

## Architecture

The tool uses a two-layer architecture: a Python CLI layer and a Kitty kitten layer.

**Python CLI Layer** (`src/ai_comm/`):

- `cli.py` - Typer CLI entry point with two command groups: Workflow (for AI) and Debug (for humans)
- `registry.py` - Single source of truth for CLI metadata (CLIInfo dataclass)
- `kitten_client.py` - Subprocess wrapper calling `kitty @ kitten` commands
- `polling.py` - Content stabilization detection via hash comparison
- `services/interaction.py` - InteractionService: unified send/wait/fetch orchestration
- `adapters/` - CLI-specific adapters for message formatting and response parsing
- `commands/` - CLI command implementations

**Kitty Kitten Layer** (`src/ai_comm/kitten/ai_comm_kitten.py`):

- Runs inside Kitty process via `@result_handler(no_ui=True)`
- Accesses Boss API for window operations (get-text, send-text, send-key, check-idle, list-ai-windows)
- Returns JSON results to the Python layer

**Key data flow:**

1. `ai-comm send` → `InteractionService.send_and_wait()`
2. `InteractionService` → `AIAdapter.format_message()` (adds sender header)
3. `KittenClient._call()` → subprocess `kitty @ kitten ai_comm_kitten.py`
4. Kitten runs inside Kitty, accesses Boss API, returns JSON
5. `polling.wait_for_idle()` polls via hash comparison until content stabilizes
6. `AIAdapter.fetch_response()` → `extract_last_response()` parses terminal output

## Adding a New CLI

1. Add entry in `src/ai_comm/registry.py` → `CLI_REGISTRY` with CLIInfo
2. Add detection in `src/ai_comm/kitten/ai_comm_kitten.py` → `AI_CLI_NAMES` dict
3. Create `src/ai_comm/adapters/<cli_name>.py` with class `{Name}Adapter` extending `AIAdapter`:
   - Set `name` class variable matching registry key
   - Optionally set `STATUS_INDICATORS` (lines to skip during parsing)
   - Optionally set `BASE_INDENT` (indentation to strip)
   - Override `extract_last_response(text: str) -> str` for parsing logic
   - Use `ResponseCollector` helper for multi-block response tracking
   - Optionally override `format_message()` for CLI-specific prefixes (e.g., Aider’s `/ask`)
   - Optionally override `fetch_response()` for alternative data sources (e.g., OpenCode reads from session export)

Adapters are loaded dynamically via `importlib`. Class name must follow convention: `{name.capitalize()}Adapter`.
