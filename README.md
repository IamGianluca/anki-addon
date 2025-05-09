A simple plugin to refactor notes in Anki with the help of LLMs.


# Usage

To use the plugin, you must set the following environment variables.
```bash
export OPENAI_HOST=your_host_url
export OPENAI_PORT=your_host_port
export OPENAI_MODEL=your_llm_model
```


# Structure

```
src/addon/
├── domain/           # Core domain models, entities, value objects
├── application/      # Application services, use cases
├── infrastructure/   # External systems adapters, repositories
...
```
