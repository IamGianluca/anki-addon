# Contributing

This is an open-source project and contributors are welcome!

## Prerequisites

- Python 3.13+ (the version Anki 26.x embeds)
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

The project uses dependency injection to keep tests fast and free of mocks. Adapters accept their external dependencies as optional `__init__` parameters defaulting to the real implementation; test callers inject fakes from `tests/fakes/` through the constructor. Never subclass or monkey-patch, and never put fakes in production code.

See [AGENTS.md](AGENTS.md) for the full port-and-adapters convention.

### Unit, integration, and e2e tests

Unit tests need no configuration and run in seconds:

```bash
make test              # unit tests only (fast)
make test_with_coverage
```

Integration tests (OpenAI-compatible server, OpenCode Go, Qdrant) and
e2e tests need a running endpoint. Set the environment variables in an
`.envrc` file in the project folder:

```bash
export OPENAI_HOST=your_host_url
export OPENAI_PORT=your_host_port
export OPENAI_MODEL=your_llm_model
# If the server requires auth (e.g. vLLM with --api-key):
export OPENAI_API_KEY=your_key
```

then run the full suite:

```bash
make test_slow         # unit + integration + e2e
```

The test suite has intentional time baselines (`scripts/gate_test_time.py`).
**Never update a baseline** after making code changes — a timing failure is
a signal to investigate, not a value to adjust.

### LLM evals

`tests/evals/` is an LLM-in-the-loop harness for the curation agent:
each task seeds a fake note repository, runs the real agent against a
real LLM, and grades the outcome with deterministic checks plus an
LLM judge. Evals are opt-in (slow, non-deterministic, spend tokens):

```bash
make eval              # capability (report-only) + regression (must pass) suites
make eval_capability   # report-only — a hill to climb
make eval_regression   # pass^k gates — pre-merge/CI guard
make eval_summary      # summarize the latest run
make eval_snapshot     # write scores into tests/evals/scores.md
```

Full details in [tests/evals/README.md](tests/evals/README.md).

### Trace review (error analysis)

Every production curation session writes a trace to `traces/`. The
trace viewer renders them with annotations, a failure-mode taxonomy,
and a review batch queue — this is the workflow for deciding what the
agent gets wrong and encoding it as eval tasks:

```bash
make trace_viewer      # http://127.0.0.1:5000
uv run python tests/evals/sample_batch.py   # pick a fresh review batch
```

Mine rejected sessions as new eval tasks (see
[AGENTS.md](AGENTS.md) → "Trace Review Workflow").

## Pre-commits

`pre-commit` is installed as part of the dev dependencies. It runs code formatting, linting, and type-checking. All Pull Requests must pass these checks (they run as part of CI).

Pre-commits also run before you create a commit locally. You can run them manually at any time:

```bash
pre-commit run --all-files
```

Other useful checks:

```bash
make format            # ruff lint (auto-fix) + format
make static_check      # ty type checker
make type_check        # mypy: verifies the Anki adapter satisfies our Protocols
```

## Architecture and Conventions

For architecture (A-Frame layout), import strategies, testing patterns, and coding principles, see [AGENTS.md](AGENTS.md).