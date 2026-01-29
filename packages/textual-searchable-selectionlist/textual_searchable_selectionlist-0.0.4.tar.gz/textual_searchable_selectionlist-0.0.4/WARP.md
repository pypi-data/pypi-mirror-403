# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A Textual widget library that adds search functionality to Textual's SelectionList widget. The widget provides case-insensitive substring filtering, supports single and multiple selection modes, and offers an API for programmatic selection in terminal-based applications.

## Development Commands

### Task Runner
This project uses `typer-invoke` to organize development tasks into admin modules. The configuration is in `pyproject.toml` under `[tool.typer-invoke]`.

Run tasks using Python module syntax:
```bash
python -m admin.lint --help
python -m admin.build --help
python -m admin.pip --help
```

### Linting and Formatting
All linter configurations are in `pyproject.toml`.

Run all linters in sequence:
```bash
python -m admin.lint all
```

Run individual linters:
```bash
python -m admin.lint black .
python -m admin.lint isort .
python -m admin.lint flake8 .
python -m admin.lint mypy .
```

### Building and Publishing

Clean build artifacts:
```bash
python -m admin.build clean
```

Update version (interactive or with flags):
```bash
python -m admin.build version --bump patch
python -m admin.build version --version 1.2.3
```

Build and publish package:
```bash
python -m admin.build publish
```

### Package Management

Compile requirements files (uses pip-compile):
```bash
python -m admin.pip compile
python -m admin.pip compile --clean
```

Sync environment with requirements:
```bash
python -m admin.pip sync
```

Install requirements:
```bash
python -m admin.pip install
```

### Testing

There are currently no automated unit tests. Manual testing can be done by running:
```bash
python tests/manual/searchable_selection_list_select.py
```

## Code Architecture

### Core Components

**SearchableListWidget** (`searchable_list_widget.py`)
- Main widget that combines a search Input with a SelectionList
- Handles keyboard navigation (arrow keys, enter, escape, ctrl+space/a/d)
- Implements real-time filtering by disabling non-matching options
- Generic over SelectionType for type safety
- Key behavior: when focused on SelectionList, alphanumeric keys are routed to the search input

**SearchableListApp** (`searchable_list_app.py`)
- Textual App wrapper for SearchableListWidget
- Provides full-screen or inline display modes
- Returns selected items via app.exit()
- Handles SelectionStrategy.ALL by immediately exiting with all items

**SelectionStrategy** (`options.py`)
- Enum defining selection modes: MULTIPLE, ONE, ALL, FAIL
- MULTIPLE/ALL: Allow selecting multiple items
- ONE: Single selection mode (deselects others when selecting)
- FAIL: Raises ValueError if multiple selections provided

**select() function** (`select.py`)
- High-level API for quick item selection
- Returns list of selected items
- Supports string, tuple, or Selection objects as input
- Includes select_enum() helper for selecting from Python enums

### Module Structure
```
src/textual_searchable_selectionlist/
├── __init__.py              # Version info
├── searchable_list_widget.py # Core widget implementation
├── searchable_list_app.py    # Textual app wrapper
├── options.py                # Selection mode enum and filtering options
└── select.py                 # High-level selection API

admin/                        # Development task modules
├── __init__.py              # Project constants (PROJECT_ROOT, SOURCE_DIR)
├── utils.py                 # Shared utilities (run, logger, etc.)
├── build.py                 # Build, version, and publish tasks
├── lint.py                  # Linting tasks
├── pip.py                   # Package management tasks
└── requirements/            # Requirements files (.in and .txt)
```

### Key Design Patterns

**Filtering mechanism**: Items are filtered by setting `option.disabled = not is_match` rather than removing them from the list, preserving indices.

**Keyboard routing**: When SelectionList is focused, single alphanumeric keypresses are intercepted and forwarded to the search Input via `input_widget.post_message(event)`.

**Callback-based selection**: Widget accepts `selected_callback` that's invoked on Enter key, receiving the list of selected items.

**Build system**: Uses flit for building/publishing. Version is tracked in both `pyproject.toml` and `src/textual_searchable_selectionlist/__init__.py`.

## Code Style

- Follow PEP8 with 100 character line limit (enforced by black)
- Single quotes for strings, triple double quotes for docstrings
- Python 3.12+ syntax and type hints (use `str | None` not `Optional[str]`)
- 4 spaces for indentation
- Line endings: LF (Unix style, see `.editorconfig`)
- Docstrings and comments in reStructuredText format
