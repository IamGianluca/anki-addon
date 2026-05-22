# AGENTS.md

Guidance for coding agents working in this repository.

This project is an Anki add-on that uses LLMs to refactor and improve flashcard notes.

## Version Control

This repository uses **jj (Jujutsu)**, not git. Use `jj` commands instead of `git`:

- `jj log` instead of `git log`
- `jj diff` instead of `git diff`
- `jj commit` instead of `git commit`
- `jj status` instead of `git status`

Do not use `git` commands — they will not work correctly.

## Development Commands

```bash
make install                        # Install dependencies with uv
make test                           # Run unit tests only (fast)
make test_with_coverage             # Run unit tests with coverage report
make test_slow                      # Run all tests (unit + integration + e2e)
make format                         # Run ruff linting (with auto-fix) + formatting
make static_check                   # Run type checker (ty)
make type_check                     # Run type checker (mypy)
pre-commit run --all-files          # Run linting (ruff)

# Run a single test file or test
uv run pytest tests/unit/test_format_notes.py
uv run pytest tests/unit/test_format_notes.py::test_function_name
uv run pytest -k "test_name_pattern"
```

## Test Time Baselines

**Never update test time baselines** after making code changes. If a timing test fails because the baseline is off, note the failure but do not adjust the baseline values. The baselines are intentional constraints, not targets to chase.

## Architecture

The project uses **A-Frame architecture**: Domain and Infrastructure are peers at the base, with Application on top orchestrating both.

```
              Application
             /           \
          Domain        Infrastructure
```

- **Domain** (`src/addon/domain/`): Core entities, value objects, repository interfaces. No imports from application or infrastructure layers.
- **Infrastructure** (`src/addon/infrastructure/`): Adapters for external systems — LLM client, Qdrant vector DB, PyQt6 UI, config loading. No imports from application or domain layers.
- **Application** (`src/addon/application/`): Use cases and services that orchestrate domain logic and infrastructure adapters.

The add-on entry point is `__init__.py` at the repo root, which Anki loads directly from the add-ons folder.

### Project Layout

```
src/addon/
├── domain/
│   ├── entities/            # Core domain entities with identity
│   ├── value_objects/       # Immutable concepts without identity
│   ├── repositories/        # Repository interfaces (ports)
│   └── services/            # Domain services
├── application/
│   ├── use_cases/           # Application use cases
│   └── services/            # Application services
└── infrastructure/
    ├── configuration/       # Config loading
    ├── external_services/   # LLM client (OpenAI-compatible)
    ├── llm/                 # Pydantic schemas for LLM structured output
    ├── persistence/         # Qdrant vector DB adapter
    ├── services/            # Infrastructure services
    └── ui/                  # PyQt6 UI components
```

## Key Patterns

### Import Strategy (critical for test performance)

The codebase uses three import strategies to keep the test suite fast:

1. **Relative imports** throughout add-on source (not tests). Anki loads the add-on directly from the add-ons folder, not as an installed package, so relative imports are required for proper module resolution:
   ```python
   from ...domain.entities.note import AddonNote
   from ...infrastructure.external_services.openai import OpenAIClient
   ```

2. **`TYPE_CHECKING` guards** for `anki`, `qdrant_client`, and `torch` — these libraries add seconds of startup overhead but are only needed for type annotations:
   ```python
   from __future__ import annotations  # required: defers annotation evaluation
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from anki.collection import Collection
       from anki.notes import Note

   def is_note_marked_for_review(col: Collection, note_id: int) -> bool:
       # At runtime, 'Collection' is a string due to __future__ annotations
       ...
   ```
   The `from __future__ import annotations` is essential — it delays evaluation of type hints, allowing forward references without runtime imports.

3. **Lazy imports inside functions** for GUI modules (`aqt`, `PyQt6`) — deferred until the code path executes:
   ```python
   def open_review_editor() -> None:
       from aqt import mw
       from PyQt6.QtWidgets import QDialog

       dialog = QDialog(mw)
       ...
   ```

### Port-and-Adapters with Dependency Injection

The application layer depends on **protocols** (ports); the infrastructure layer provides **concrete implementations** (adapters).

**Ports** are `Protocol` classes that define minimal contracts. They live in the layer that consumes them:

- `DocumentRepository` (`domain/repositories/`) — document storage and search
- `LLMClient` (`application/protocols.py`) — language model interaction
- `ConfigProvider` (`infrastructure/protocols.py`) — reading addon configuration (lives in infrastructure because it adapts Anki's `AddonManager`, not a domain concept)

**Adapters** are concrete classes that implement ports. They live in the infrastructure layer:

- `QdrantDocumentRepository` — implements `DocumentRepository` via Qdrant
- `OpenAIClient` — implements `LLMClient` via HTTP to OpenAI-compatible endpoints

**Factory with optional overrides** is the uniform construction strategy. Every adapter has a `create()` factory that accepts optional keyword arguments for all external dependencies. Production callers omit them for real defaults; test callers pass fakes:

```python
# Production — factory supplies real defaults
repo = QdrantDocumentRepository.create(encoder)
client = OpenAIClient.create(config)

# Tests — override dependencies via keyword arguments
repo = QdrantDocumentRepository.create(
    encoder, client=FakeQdrantClient(search_responses=[...])
)
client = OpenAIClient.create(config, http_client=FakeHttpClient(json_body=...))
```

Always use `.create()` — never call `__init__` directly.

**Fakes** live in `tests/fakes/`, never in production code:

- `FakeQdrantClient`, `FakeSentenceTransformer` (`tests/fakes/qdrant_fakes.py`)
- `FakeHttpClient`, `FakeLLMClient` (`tests/fakes/openai_fakes.py`)
- `FakeAddonManager`, `FakeCollection`, `FakeNote` (`tests/fakes/aqt_fakes.py`)

Fakes are production-like classes that behave predictably without real I/O. They are **not** mocks — they implement real logic (e.g. `FakeQdrantClient` tracks stored documents and returns configured search responses).

**File-based adapters** (e.g. `JSONLTrainingDataset`) use pytest `tmp_path` fixtures instead of fakes — testing against real file I/O with a temporary location is simpler than inventing a fake filesystem.

### LLM Integration

`OpenAIClient` (`infrastructure/external_services/openai.py`) uses structured output (Pydantic schema in `infrastructure/llm/schemas.py`) with reasoning to generate `AddonNoteChanges`. Configuration is loaded via `AddonConfig` from Anki's addon manager.

## Bundling Dependencies

Anki loads add-ons but does not install them as Python packages. External dependencies must be bundled and compiled for Python 3.9 (Anki's embedded interpreter), even if development uses a newer version:

```bash
./bundle_dependencies.sh  # creates ./vendor/ with pydantic, qdrant-client, and dependencies
```

This script creates a Python 3.9 virtual environment, installs the required packages, and copies them to `./vendor/`.

## Core Principles

This project follows principles from "A Philosophy of Software Design" by John Ousterhout.

### Deep Modules
- Simple interfaces hiding complex implementations
- Significant functionality through narrow interfaces

### Comments
- Only write comments that add non-obvious information
- Explain "why", not "what"; remove comments that restate the code

### Naming
- Precise, descriptive names that capture essence
- Avoid vague names like `manager`, `handler` when specific terms exist

### Testing
- No mocks — use fakes from `tests/fakes/` (see Port-and-Adapters section)
- Tests should be sociable — exercise real code paths through collaborating objects
- Use Given / When / Then structure in every test
- **Adapter tests** inject fakes at the outermost infrastructure boundary (e.g. `FakeHttpClient` for `OpenAIClient`), exercising the adapter's real logic
- **Service-layer tests** inject fakes at the port level (e.g. `FakeLLMClient` for `NoteFormatter`), bypassing adapter internals entirely
