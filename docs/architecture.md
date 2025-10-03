## Project Structure

The project adopts Domain-Driven Design principles with a clear separation between domain, application, and infrastructure layers:

```
addon/
├── domain/            # Core domain models, entities, value objects
│   ├── models/
│   └── services/
├── application/       # Application services, use cases
│   └── services/
└── infrastructure/    # External systems adapters, repositories
    ├── adapters/
    └── repositories/
```

The domain model should not have any dependencies with application and infrastructure layers. One rule of thumb to check that is to look at the imports. Make sure you are not importing anything from application and infrastructure layers when working on the domain layer. 

This separation is not arbitrary. Having a domain layer without application and infrastructure dependencies gives us more freedom to test things rapidly, and keeps the logic simple.

For more information on the architectural patterns used in this project, see [Architecture Patterns in Python](https://www.cosmicpython.com/).

### Development Gotchas

#### Relative Imports

You will notice that we use relative imports instead of absolute across the entire add-on codebase, with the exclusion of the test suite. This is needed since Anki will not install the add-on as a library, but instead loads it directly from the add-ons folder, requiring relative imports for proper module resolution:

```python
from datetime import datetime

from anki.notes import Note

from ...domain.models.completion_result import CompletionResult
from ...infrastructure.openai import OpenAIClient
```


#### Type-Only Imports

Importing the `anki` library adds several seconds to test suite startup due to its heavy dependencies. To optimize this, we use `TYPE_CHECKING` guards to defer imports that are only needed for type annotations. These imports execute during type checking but are skipped at runtime.

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

The `from __future__ import annotations` is essential: it delays evaluation of type hints, allowing forward references without runtime imports.



#### Lazy Imports

For expensive runtime imports (especially GUI modules like `aqt` and PyQt6), we use lazy imports inside functions. This defers the import cost until the code path is actually executed.

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

Anki loads addons, but does not install them as Python packages. For this reason, we need to bundle any external dependencies not included with Anki. These dependencies must be compiled with Python 3.9, as that is the Python interpreter version used by Anki. To bundle the required dependencies, use the provided script:

```bash
./bundle_dependencies.sh
```

This script creates a Python 3.9 virtual environment, installs `pydantic` and its dependencies, and copies them to the `./vendor` directory.
