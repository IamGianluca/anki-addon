#### New features

- [ ] Add option to change note type from editing window
- [ ] Use semantic search instead of lexical search in search bar
- [ ] Identify notes that are not atomic
- [ ] Identify isolated notes — these will be harder to learn 
- [ ] ...

#### Bugs

- [ ] Code snippets are sometimes removed
- [ ] Back card is sometimes not changed
- [ ] Images are sometimes removed
- [ ] ... 

#### Refactoring

- [ ] Refactor main classes involved in note formatting workflow to reduce cognitive load
- [ ] Refactor system prompt for note formatting workflow to be more readable for humans
- [ ] ...

#### Performance

- [ ] Switch to more performant LLM that still fits in 24GB VRAM GPU
- [ ] Review system prompt and few shot examples to match current format style
- [ ] Make sure we are using prefix caching in vLLM
- [ ] Create an agent: often, an agent can do a better job compared to a simple completion call. Notes are never introduced in isolation. It can be beneficial for an agent to review existing notes, and even suggest splitting a note into multiple notes, change note type, or more sophisticated operations
- [ ] ...

#### Testing
- [ ] Investigate `tests/e2e/test_format_note_workflow.py::test_complete_format_workflow_for_basic_note`. Takes 0.06s. Might contain calls to infra.
- [ ] ...
