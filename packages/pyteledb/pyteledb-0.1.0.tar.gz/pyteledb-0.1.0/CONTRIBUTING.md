# Contributing to pyteledb

Thank you for your interest in contributing to pyteledb! This document provides guidelines and context for contributors.

## Core Philosophy

**pyteledb is a Telegram-native persistence abstraction, not a general-purpose database.**

Before contributing, please internalize this mental model:
- Telegram itself **is** the persistence layer
- Only the **Telegram Bot API** is used — no MTProto, no user accounts
- No external database is required
- Optional local cache (memory/SQLite) is allowed for performance

## Non-Negotiable Constraints

Any contribution that violates these constraints will be rejected:

1. **No external state** — All persistent state must live in Telegram
2. **No MTProto** — Bot API only
3. **No hidden complexity** — All operations must be explicit and inspectable
4. **No full chat scans** — Only fetch required message IDs
5. **Crash-resilient writes** — All writes must be idempotent and retry-safe

## Project Structure

Each directory has a specific responsibility. Please maintain these boundaries:

```
pyteledb/
├── core/       # Telegram-native DB logic (database, record, pointers, etc.)
├── telegram/   # STRICT Bot API boundary (client, messages, files, pins)
├── storage/    # Encoding & integrity (schema, serializer, checksum)
├── cache/      # Ephemeral acceleration (memory, sqlite)
├── ops/        # Operational safety (queue, throttling, metrics)
├── utils/      # Utilities (time, ids, logging)
└── exceptions.py
```

## Development Setup

```bash
# Clone the repository
git clone https://github.com/SilentDemonSD/pyteledb.git
cd pyteledb

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check pyteledb/

# Run type checking
mypy pyteledb/

# Run tests
pytest tests/ -v
```

## Code Style

- **Type hints**: All public functions must have type annotations
- **Docstrings**: Use Google-style docstrings
- **Line length**: 100 characters max
- **Formatting**: We use `ruff` for linting and formatting

## Pull Request Checklist

Before submitting a PR:

- [ ] Code follows the Telegram-native philosophy
- [ ] No violations of hard constraints
- [ ] Respects directory boundaries
- [ ] Type hints on all public interfaces
- [ ] Tests for new functionality
- [ ] Documentation updated if needed
- [ ] `ruff check` passes
- [ ] `mypy` passes

## Good First Issues

Look for issues labeled `good-first-issue` for beginner-friendly contributions.

## Questions?

Open an issue or discussion if you're unsure about the architectural fit of your contribution.
