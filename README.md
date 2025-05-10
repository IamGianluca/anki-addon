A simple plugin to refactor notes in Anki with the help of LLMs.


# Usage

After adding the addon to your addon folder, start `anki`. You will need to go to `Tools > Addons`, select the plugin, and then `Config`. There you will need to fill the necessary secrets to connect to the OpenAI-compatible inference server. 

# Contributing

To run the test suite, you must first set the following environment variables:

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
