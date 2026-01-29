# linear-term

[![CI](https://github.com/tjburch/linear-term/actions/workflows/ci.yml/badge.svg)](https://github.com/tjburch/linear-term/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/license-PolyForm%20Noncommercial-orange.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg)](https://buymeacoffee.com/tylerjamesburch)

A terminal user interface for [Linear](https://linear.app) project management. Manage issues, triage your inbox, and track projects without leaving the terminal.

## Features

- **3-panel TUI**: Navigate projects/cycles in the sidebar, browse issues in the list, and view details in the right panel
- **Kanban board**: Visual board view grouped by workflow state
- **Triage workflow**: Dedicated mode for processing untriaged issues with quick actions
- **CLI commands**: Scriptable interface for listing, viewing, creating, and searching issues
- **Offline-ready**: SQLite cache for instant startup and offline browsing
- **Themeable**: 9 built-in color schemes

## Installation

```bash
pip install -e .
```

## Configuration

### API Key

Set your Linear API key via environment variable:

```bash
export LINEAR_API_KEY=lin_api_xxxxx
```

Or create a config file at `~/.config/linear-term/config.yaml`:

```yaml
api_key: lin_api_xxxxx
```

### Full Configuration Example

```yaml
api_key: $LINEAR_API_KEY  # Uses env var

appearance:
  theme: material-dark  # See themes below

layout:
  sidebar_width: 28
  detail_panel_width: 40
  show_detail_panel: true
  show_sidebar: true

defaults:
  view: my-issues       # Starting view
  sort_by: priority     # priority, status, updated, created
  sort_order: asc

columns:                # Issue list columns
  - identifier
  - title
  - status
  - priority
  - assignee

kanban:
  columns:              # Custom column order (empty = all states)
    - Backlog
    - Todo
    - In Progress
    - In Review
    - Done
  hide_done: false      # Hide completed/canceled

cache:
  ttl_minutes: 30

editor:
  command: vim          # For editing descriptions (defaults to $EDITOR)
```

### Available Themes

`material-dark` (default), `gruvbox-dark`, `linear`, `dracula`, `nord`, `solarized-dark`, `catppuccin-mocha`, `one-dark`, `tokyo-night`

## Usage

### Interactive TUI

Launch the full terminal interface:

```bash
linear-term
```

The TUI provides three main views:
- **List view**: Traditional issue list with sortable columns
- **Kanban view**: Board layout grouped by status (press `b` to toggle)
- **Triage view**: Process untriaged issues from your inbox

### CLI Commands

Use standalone commands for quick operations or scripting:

```bash
# List issues
linear-term list                    # All issues (20 max)
linear-term list --mine             # Only issues assigned to you
linear-term list --limit 50         # Specify max results
linear-term list --json             # Output as JSON

# View issue details
linear-term view ENG-123            # By identifier
linear-term view ENG-123 --json     # JSON output

# Create issues
linear-term create "Fix login bug"
linear-term create "Add feature" --description "Details here"
linear-term create "Task" --team Engineering --priority high

# Search
linear-term search "auth bug"
linear-term search "payment" --limit 10 --json
```

#### Command Reference

| Command | Aliases | Description |
|---------|---------|-------------|
| `list` | `ls` | List issues |
| `view` | `show` | View issue details |
| `create` | `new` | Create a new issue |
| `search` | — | Search issues |

#### Common Options

| Option | Commands | Description |
|--------|----------|-------------|
| `--json` | all | Output as JSON for scripting |
| `--limit N` | list, search | Maximum results (default: 20) |
| `--mine` | list | Only your assigned issues |
| `--team NAME` | create | Target team name or key |
| `--priority LEVEL` | create | urgent, high, medium, low, none |
| `--description TEXT` | create | Issue description |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/

# Format check
ruff format --check src/
```

## License

[PolyForm Noncommercial 1.0.0](LICENSE)
