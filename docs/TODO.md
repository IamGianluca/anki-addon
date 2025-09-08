#### New features

- [ ] Add option to change note type from editing window
- [ ] Use semantic search instead of lexical search in search bar
- [ ] Identify notes that are not atomic
- [ ] Identify isolated notes ― these will be harder to learn 
- [ ] ...

#### Refactoring

- [ ] Refactor main classes involved in note formatting workflow to reduce cognitive load
- [ ] ...

#### Performance

- [ ] Convert tests in `tests/integration/test_qdrant_integration.py::test_overlapping_sociable_behavior_with_real_dependencies` to proper **narrow** integration tests. It currently takes over 30 seconds to run
- [ ] Convert tests in `tests/integration/test_qdrant_integration.py::test_real_qdrant_performance_characteristics` to proper **narrow** integration tests. It currently takes over 3 seconds to run
- [ ] Investigate better LLM to use instead of `meta-llama/Meta-Llama-3.1-8B-Instruct`
- [ ] ...
