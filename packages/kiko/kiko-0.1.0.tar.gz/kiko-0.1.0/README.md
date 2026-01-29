# Project kiko (機巧)

A small interactive CLI playground built with Prompt Toolkit and Rich.

## Features
- Slash-command interface (e.g., `/help`, `/echo`)
- Rich UI panels and tables
- Persistent config with schema versioning
- Package-based version display
- JSONL session logging per project

## Requirements
- Python 3.12+
- `uv` (recommended) or another Python environment manager

## Install

### Using uv (recommended)
```bash
uv sync
```

### Editable install (optional)
```bash
uv pip install -e .
```

## Run

### Local development
```bash
uv run kiko
# or
make dev
```

### Resume a session
```bash
kiko resume <session_id>
# or
kiko --resume <session_id>
```

### Execute once
```bash
kiko exec "/help"
kiko exec "hello"
```

### Build
```bash
uv build
# or
make build
```

## Commands
- `/help` - Show command list
- `/exit` - Exit the application
- `/quit` - Alias for `/exit`
- `/clear` - Clear the screen
- `/time` - Show current local time
- `/sysinfo` - Show system information
- `/echo <message>` - Echo a message
- `/say <message>` - Render a chat message panel
- `/commands [--pretty]` - Output command metadata as JSON
- `/session` - Show current session information
- `/sessions` - List sessions for the current project
- `/resume <session_id>` - Resume a previous session

## Shortcuts
- `Tab` (with empty input) - Toggle thinking mode

## Configuration
On first run, the app creates a config file at:

```
~/.config/kiko/config.json
```

The config uses a schema version for safe upgrades. Example:
```json
{
  "schema_version": 1,
  "last_seen_app_version": "0.1.0"
}
```

## Sessions
Each run creates a JSONL session file scoped to the current project. Sessions are
stored under:

```
~/.config/kiko/sessions/<project_id>/<session_id>.jsonl
```

Use `/session` to view the active session ID, `/sessions` to list sessions for
the current project, and `/resume <session_id>` to continue a past session.

## Versioning
The displayed version is resolved from the installed package metadata.
If the package metadata is unavailable, the version falls back to `0.0.0`.

## Lint
```bash
uv run ruff check src
```

## Tests
No tests are defined yet.

## License
TBD.
