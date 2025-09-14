# Claude Code Guidelines

This project follows principles from "A Philosophy of Software Design" by John Ousterhout.

## Core Principles

### Deep Modules
- Design modules with simple interfaces that hide complex implementations
- Each module should provide significant functionality through a narrow interface

### Information Hiding
- Hide implementation details behind clean abstractions
- Minimize dependencies between modules

### Comments and Documentation
- **Only write comments/docstrings that add non-obvious information**
- Focus on explaining "why" rather than "what"
- Remove redundant comments that restate the code

### Naming
- Use precise, descriptive names that capture essence
- Avoid vague names like `manager`, `handler` when specific terms exist

## Architecture

### Layers
- **Domain** (`src/addon/domain/`): Core business logic, entities, interfaces
- **Application** (`src/addon/application/`): Use cases orchestrating domain logic
- **Infrastructure** (`src/addon/infrastructure/`): External services, UI, configuration

Dependencies flow inward: Infrastructure → Application → Domain

## Development Commands

```bash
make test                   # Run unit tests
make test_slow              # Run all tests
pre-commit run --all-files  # Run linting
```

Remember: Simple interfaces, complex implementations. Ask "does this comment add value that isn't obvious from the code?"
