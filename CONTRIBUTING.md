# Contributing

This is an open-source project and contributors are welcome!

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (recommended package manager)

## Setup

1. Clone the repository
    ```bash
    git clone https://github.com/IamGianluca/anki-addon.git
    cd anki-addon
    ```
2. Create and sync the Python virtual environment
    ```bash
    make install
    ```
3. Activate the virtual environment (e.g., `source .venv/bin/activate` or via your IDE).

## Testing

This project follows a testing approach similar to what's described in [Testing without Mocks](https://www.jamesshore.com/v2/projects/nullables/testing-without-mocks).

To run the test suite:

1. Set the needed environment variables by creating an `.envrc` file in the project folder. Don't forget to set the appropriate values for your local development environment.
   ```bash
   export OPENAI_HOST=your_host_url
   export OPENAI_PORT=your_host_port
   export OPENAI_MODEL=your_llm_model
   ```

2. Run the tests:
   ```bash
   make test        # run unit tests
   make test_slow   # run unit, integration, and end-to-end tests
   ```

## Pre-commits

`pre-commit` is installed as part of the dev dependencies. It runs code formatting, linting, and type-checking. All Pull Requests must pass these checks (they run as part of CI).

Pre-commits also run before you create a commit locally. You can run them manually at any time:

```bash
pre-commit run --all-files
```

## Project Structure

The project adopts Domain-Driven Design principles with a clear separation between domain, application, and infrastructure layers:

```
src/addon/
├── domain/
│   ├── entities/            # Core domain entities with identity
│   ├── value_objects/       # Immutable concepts without identity
│   ├── repositories/        # Repository interfaces
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

The domain model should not have any dependencies on application and infrastructure layers. A practical rule of thumb: check the imports. You should never import from application or infrastructure layers when working on the domain layer.

A domain layer free of application and infrastructure dependencies keeps logic pure — no I/O, no networking — which makes it easier to test and reason about.

For more information on the architectural patterns used in this project, see [Architecture Patterns in Python](https://www.cosmicpython.com/) and [docs/architecture.md](docs/architecture.md).

### Development Gotchas

#### Relative Imports

The add-on source uses relative imports (tests use absolute imports). Anki loads the add-on directly from the add-ons folder, not as an installed package, so relative imports are required for proper module resolution:

```python
from datetime import datetime

from anki.notes import Note

from ...domain.models.completion_result import CompletionResult
from ...infrastructure.openai import OpenAIClient
```

#### Type-Only Imports

Importing the `anki` library adds several seconds to test suite startup due to its heavy dependencies. Use `TYPE_CHECKING` guards to defer imports that are only needed for type annotations:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.notes import Note

def is_note_marked_for_review(col: Collection, note_id: int) -> bool:
    # At runtime, 'Collection' is a string due to __future__ annotations
    # The actual import only happens during type checking (mypy, pyright, etc.)
    ...
```

The `from __future__ import annotations` is essential — it delays evaluation of type hints, allowing forward references without runtime imports.

#### Lazy Imports

For expensive runtime imports (especially GUI modules like `aqt` and PyQt6), use lazy imports inside functions. This defers the import cost until the code path is actually executed:

```python
def open_review_editor() -> None:
    # Only import GUI dependencies when this function is called
    from aqt import mw
    from aqt.utils import showInfo
    from PyQt6.QtWidgets import QDialog, QPushButton

    dialog = QDialog(mw)
    ...
```

#### Bundling Dependencies

Anki loads add-ons but does not install them as Python packages. External dependencies must be bundled and compiled with Python 3.9 (Anki's interpreter version):

```bash
./bundle_dependencies.sh
```

This script creates a Python 3.9 virtual environment, installs `pydantic` and its dependencies, and copies them to the `./vendor` directory.
