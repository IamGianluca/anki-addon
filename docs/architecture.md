# Architecture

The project uses **A-Frame architecture**: Domain and Infrastructure are peers at the base, with Application on top orchestrating both.

```
              Application
             /           \
          Domain        Infrastructure
```

```
src/addon/
├── domain/
│   ├── entities/            # Core domain entities with identity
│   ├── repositories/        # Repository ports (interfaces)
│   └── services/            # Domain services
├── application/
│   ├── protocols.py         # Ports consumed by the application layer (e.g. CompletionProvider)
│   ├── use_cases/           # Application use cases
│   └── services/            # Application services
└── infrastructure/
    ├── protocols.py         # Ports for external systems (HttpClient, ConfigProvider, QdrantDriver)
    ├── configuration/       # Config loading
    ├── external_services/   # LLM client (OpenAI-compatible)
    ├── llm/                 # Pydantic schemas for LLM structured output
    ├── persistence/         # Qdrant vector DB adapter
    ├── services/            # Infrastructure services
    └── ui/                  # PyQt6 UI components
```

Dependency rules — a practical rule of thumb: check the imports.

- **Domain** imports nothing from the other layers. A domain layer free of application and infrastructure dependencies keeps logic pure — no I/O, no networking — which makes it easier to test and reason about.
- **Infrastructure** implements the ports defined in the domain and application layers, so it imports those port definitions (and the domain entities they reference). The domain layer never imports infrastructure.
- **Application** is the only layer that may import both: use cases wire concrete adapters to ports, acting as the composition root.

For more information on the architectural patterns used in this project, see [Architecture Patterns in Python](https://www.cosmicpython.com/).

## Entry Point

The add-on entry point is `__init__.py` at the repo root. Anki loads the add-on directly from the add-ons folder (not as an installed package), so the root `__init__.py` sets up the vendor path and bootstraps the add-on.

For development-specific details (import strategies, bundling), see [CONTRIBUTING.md](../CONTRIBUTING.md).
