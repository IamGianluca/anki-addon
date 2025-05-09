A simple plugin to refactor notes in Anki with the help of LLMs.


# Usage

To use the plugin, you must set the following environment variables.
```bash
export OPENAI_HOST=your_host_url
export OPENAI_PORT=your_host_port
export OPENAI_MODEL=your_llm_model
```


# Structure

This projects tries to adopt a Domain-Driven Design, and the project structure reflects this decision, with a clear separation between domain, application, and infrastructure layers.

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
