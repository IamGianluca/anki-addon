# Architecture

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

This separation is not arbitrary. A domain layer free of application and infrastructure dependencies keeps logic pure — no I/O, no networking — which makes it easier to test and reason about.

For more information on the architectural patterns used in this project, see [Architecture Patterns in Python](https://www.cosmicpython.com/).

## Entry Point

The add-on entry point is `__init__.py` at the repo root. Anki loads the add-on directly from the add-ons folder (not as an installed package), so the root `__init__.py` sets up the vendor path and bootstraps the add-on.

For development-specific details (import strategies, bundling), see [CONTRIBUTING.md](../CONTRIBUTING.md).
