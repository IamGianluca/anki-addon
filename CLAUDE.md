# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This project is an Anki add-on that uses LLMs to refactor and improve flashcard notes. It follows principles from "A Philosophy of Software Design" by John Ousterhout.

## Development Commands

```bash
make install                        # Install dependencies with uv
make test                           # Run unit tests only (fast)
make test_with_coverage             # Run unit tests with coverage report
make test_slow                      # Run all tests (unit + integration + e2e)
make static_check                   # Run type checker (ty)
pre-commit run --all-files          # Run linting (ruff)

# Run a single test file or test
uv run pytest tests/unit/test_format_notes.py
uv run pytest tests/unit/test_format_notes.py::test_function_name
uv run pytest -k "test_name_pattern"
```

## Architecture

Dependencies flow inward: **Infrastructure → Application → Domain**

- **Domain** (`src/addon/domain/`): Core entities, value objects, repository interfaces. No imports from application or infrastructure layers.
- **Application** (`src/addon/application/`): Use cases and services orchestrating domain logic.
- **Infrastructure** (`src/addon/infrastructure/`): LLM client (OpenAI-compatible), Qdrant vector DB, PyQt6 UI, config loading.

The add-on entry point is `__init__.py` at the repo root, which Anki loads directly from the add-ons folder.

## Key Patterns

### Import Strategy (critical for test performance)

The codebase uses three import strategies to keep the test suite fast:

1. **Relative imports** throughout add-on source (not tests) — required because Anki loads the add-on as a folder, not an installed package.

2. **`TYPE_CHECKING` guards** for `anki`, `qdrant_client`, and `torch` imports — these libraries add seconds of startup overhead but are only needed for type annotations at runtime:
   ```python
   from __future__ import annotations  # required: defers annotation evaluation
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from anki.collection import Collection
   ```

3. **Lazy imports inside functions** for GUI modules (`aqt`, `PyQt6`) — deferred until the code path executes.

### Null Object Pattern for Testing

Infrastructure classes expose a `create_null()` factory for unit tests that avoids real external dependencies (Qdrant server, sentence-transformer model loading which takes 20+ seconds). See `QdrantDocumentRepository.create_null()` as the reference implementation.

### LLM Integration

`OpenAIClient` (`infrastructure/external_services/openai.py`) uses structured output (Pydantic schema in `infrastructure/llm/schemas.py`) with reasoning to generate `AddonNoteChanges`. Configuration is loaded via `AddonConfig` from Anki's addon manager.

## Anki Deployment

Anki does not install the add-on as a Python package — external dependencies must be vendored:

```bash
./bundle_dependencies.sh  # creates ./vendor/ with pydantic compiled for Python 3.9
```

The bundled dependencies target Python 3.9 (Anki's embedded interpreter), even if development uses a newer version.

## Core Principles

### Deep Modules
- Simple interfaces hiding complex implementations
- Significant functionality through narrow interfaces

### Comments
- Only write comments that add non-obvious information
- Explain "why", not "what"; remove comments that restate the code

### Naming
- Precise, descriptive names that capture essence
- Avoid vague names like `manager`, `handler` when specific terms exist
