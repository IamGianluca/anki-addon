#### New features

- [ ] Change note type from editing window
- [ ] ...

#### Refactoring

- [ ] Starting from note formatting use case, refactor main classes to make them less obscure and reduce cognitive load
- [ ] ...

#### Performance

- [ ] Convert tests in `tests/integration/test_qdrant_integration.py::test_overlapping_sociable_behavior_with_real_dependencies` to proper **narrow** integration tests. It currently takes over 30 seconds to run
- [ ] Convert tests in `tests/integration/test_qdrant_integration.py::test_real_qdrant_performance_characteristics` to proper **narrow** integration tests. It currently takes over 3 seconds to run
- [ ] Investigate better LLM to use instead of `meta-llama/Meta-Llama-3.1-8B-Instruct`
- [ ] ...
