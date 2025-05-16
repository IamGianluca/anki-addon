## 🧑‍💻 CONTRIBUTING

### Project Structure

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

### Testing

This project follows a testing approach similar to what's described in [Testing without Mocks](https://www.jamesshore.com/v2/projects/nullables/testing-without-mocks).

To run the test suite:

1. Set up the necessary environment variables:
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

### Development Gotchas

#### Relative Imports

You will notice that we use relative imports instead of absolute across the entire add-on codebase, with the exclusion of the test suite. This is needed since Anki will not install the add-on as a library, but instead loads it directly from the add-ons folder, requiring relative imports for proper module resolution:

```python
from datetime import datetime

from anki.notes import Note

from ...domain.models.completion_result import CompletionResult
from ...infrastructure.openai import OpenAIClient
```

#### Bundling Dependencies

Anki loads addons, but does not install them as Python packages. For this reason, we need to bundle any external dependencies not included with Anki. These dependencies must be compiled with Python 3.9, as that is the Python interpreter version used by Anki. To bundle the required dependencies, use the provided script:

```bash
./bundle_dependencies.sh
```

This script creates a Python 3.9 virtual environment, installs `pydantic` and its dependencies, and copies them to the `./vendor` directory.
