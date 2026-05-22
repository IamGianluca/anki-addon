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

The project uses dependency injection to keep tests fast and free of mocks. Every adapter has a `.create()` factory that accepts optional keyword arguments to override dependencies with fakes from `tests/fakes/`.

See [AGENTS.md](AGENTS.md) for the full port-and-adapters convention.

To run the test suite:

1. Set the needed environment variables by creating an `.envrc` file in the project folder:
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

## Architecture and Conventions

For architecture (A-Frame layout), import strategies, testing patterns, and coding principles, see [AGENTS.md](AGENTS.md).
