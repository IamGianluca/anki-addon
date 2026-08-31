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
│   ├── use_cases/           # Application use cases (formatting, curation, counting, duplicates)
│   └── services/            # Application services: NoteFormatter, CuratorAgent (ReAct loop)
│                            #   + CuratorTools (agent tool surface) + CurationTraceStore
└── infrastructure/
    ├── protocols.py         # Ports for external systems (HttpClient, ConfigProvider, QdrantDriver)
    ├── configuration/       # Config loading (AddonConfig, OpenAIConfig, OpenCodeGoConfig)
    ├── external_services/   # LLM clients: OpenAIClient (self-hosted compatible servers) and OpenCodeGoClient
    ├── llm/                 # Pydantic schemas for LLM structured output
    ├── persistence/         # Qdrant vector DB adapter, AnkiNoteRepository, training datasets
    ├── services/            # Composition factories (completion provider, formatter)
    └── ui/                  # PyQt6 UI components (editor dialog, curation review dialog)
```

Dependency rules — a practical rule of thumb: check the imports.

- **Domain** imports nothing from the other layers. A domain layer free of application and infrastructure dependencies keeps logic pure — no I/O, no networking — which makes it easier to test and reason about.
- **Infrastructure** implements the ports defined in the domain and application layers, so it imports those port definitions (and the domain entities they reference). The domain layer never imports infrastructure.
- **Application** is the only layer that may import both: use cases wire concrete adapters to ports, acting as the composition root.

For more information on the architectural patterns used in this project, see [Architecture Patterns in Python](https://www.cosmicpython.com/).

## Two AI workflows

The add-on ships two LLM workflows, both built on the same
`CompletionProvider` port:

- **NoteFormatter** (one-shot): rewrites a single flagged note in one
  LLM call and shows the diff for approval.
- **CuratorAgent** (ReAct loop): given a seed note, the agent explores
  the collection through `CuratorTools` (search, read, propose
  edit/create/delete/split, review_changeset for atomicity checking)
  and accumulates a `ProposedChangeSet`. **The agent has no write
  access to the collection** — mutation tools only record proposals;
  the user approves them in a batch review dialog before anything is
  applied. Data integrity is enforced by construction: the agent
  cannot corrupt notes.

Every curation session is persisted as a trace (same record shape as
the eval harness) with the user's outcome, so rejected sessions can
be mined for error analysis.

## Entry Point

The add-on entry point is `__init__.py` at the repo root. Anki loads the add-on directly from the add-ons folder (not as an installed package), so the root `__init__.py` sets up the vendor path and bootstraps the add-on, registering the Tools-menu actions and editor buttons.

For development-specific details (import strategies, bundling), see [CONTRIBUTING.md](../CONTRIBUTING.md). The eval harness for the curation agent lives in `tests/evals/` — see [tests/evals/README.md](../tests/evals/README.md).
