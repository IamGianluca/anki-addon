# Project: Anki-addon

## Why this project exists

<!-- Be honest. Not what sounds impressive, but what I actually care about.
Brandon: "Sometimes instead of writing down my actual goals, I accidentally
write down the things that I think *should* be my goals." -->

Sub-optimal decks — cards with factual mistakes, open-ended questions, or inconsistent formatting — hurt retention. Fixing these issues in a medium deck (1,000+ cards) is prohibitively time-consuming, and that time is better spent studying or resting. At the same time, standardizing formatting or identifying duplicate cards becomes impossible to do manually as a deck grows. AI can ease this curation process while keeping the human in control of the outcome.

## Goals

<!-- Each goal should be falsifiable — I and anyone else should be able to
     agree on whether it's been met. "Make it fast" is useless. "Handle 1000
     requests/sec on my laptop" is testable. -->

1. Don't corrupt existing notes. The bugs where code snippets, images, and back cards get silently removed are data integrity issues. Every time one of these occurs, I either lose content or have to manually fix it, which erodes trust in the tool and means the user will pay more attention in reviewing the tool output, slowing her down.
2. Improve deck quality with minimal manual intervention. The tool should analyze cards and decks and provide recommendations without much input from the user — the tool is the expert on how Anki notes should look. The LLM makes individual notes better (formatting, atomicity, completeness) and curates the deck (gaps, duplicates) without the user hand-editing each note. We aim for a 90+% acceptance rate on recommended changes.
3. Keep the codebase easy to change. I'm the sole maintainer, I work on it in bursts between everything else, and I need to be able to pick it back up quickly.

### Non-goals

<!-- Just as important. What am I explicitly NOT trying to do? This is my
     defense against drift — the moment I catch myself working on something
     that serves a non-goal, stop. -->

- We are not going to support every LLM inference provider, since this is a personal project and I want to support only what I'm going to use.
- We are not going to COMPLETELY automate the creation and curation of flashcards. We believe that a minimum human intervention is required, not just to guarantee high-quality, but also to ensure human input in decisions around what needs to be included in the deck and provide to the system the necessary information to ADAPT to the individual user. Personalization is the name of the game. The deck should reflected the individual needs of the user.

## Constraints

<!-- The details that guide tradeoffs. Fill in what's relevant. -->

- **Users:** Just me.
- **Runtime:** Anki desktop client on Ubuntu & MacOS.
- **Maintenance horizon:** Next 5 years (at least).
- **Time budget:** A couple of hours per month, on average.

## Prioritized tasks

<!-- Sort by impact on the goals above, not by what's fun. For each task, I
     should be able to point at which goal it serves. If I can't, it doesn't
     belong here yet.

     Re-sort periodically. When I feel pulled toward something not in the top
     few items, that's drift — check myself against the goals. -->

### Now (highest impact)

- [ ] Keep track of metrics (e.g., number of suggestions, suggestions accepted/declined/accepted with changes) ― **Goal 2**
- [ ] Create streamlined workflow to do error analysis, in order to prioritize next actions ― **Goal 2**
- [ ] Support OpenCode Go, to get access to more capable models than what we can self-host ― **Goal 2**

### Next

- [ ] Identify notes that are not atomic and suggest fix — **Goal 2**
- [ ] Identify isolated notes — these will be harder to learn ― and suggest fix — **Goal 2**
- [ ] Support converting existing note to a different type (e.g., Basic --> Cloze, Cloze --> Basic) — **Goal 2**
- [ ] Evolve the backend approach from one-shot LLM call to an AI agent using dedicated tools ― **Goal 2**
- [ ] Add web search capability to AI agent to overcome knowledge limitation in the specific language model ― **Goal 2**
- [ ] For OpenAI-compatible servers (llama.cpp, vLLM), hide per-model quirks (e.g., thinking params, markdown fence stripping) inside `OpenAIClient` driven by `AddonConfig`. — **Goal 3**
- [ ] Expose token usage (`prompt_tokens`, `completion_tokens`) from the OpenAI API response in `OpenAIClient.run()` — **Goal 3**
- [ ] Investigate `tests/e2e/test_format_note_workflow.py::test_complete_format_workflow_for_basic_note`. Takes 0.06s. Might contain calls to infra.

### Later

- [ ] Use semantic search instead of lexical search in search bar

### Icebox (ideas, not commitments)

<!-- Things I might do someday. Kept here so they stop floating around in
     my head, but explicitly not prioritized. -->

- Improve search capability in Anki client with Qdrant (semantic search + bm25 + reranking).
- Identify _almost_ duplicate cards (e.g., semantically duplicate, partially overlapping, etc.).
- Identify gaps in the deck (e.g., missing cards covering prerequisites for more advanced topics already present in the deck, cards that can connect multiple topics).
- Generate a cluster of flashcards starting from some text/document.

## Decision log

<!-- When I make a non-obvious choice, write it down with the reasoning.
     Prevents re-litigating the same decision weeks later when I've forgotten
     why I chose what I chose. -->

| Date | Decision | Reasoning |
|------|----------|-----------|
| Q2 2025 | A-Frame architecture with Domain / Infrastructure / Application layers | Keeps domain pure; infrastructure swappable; aligns with time budget by making code easy to navigate |
| Q2 2026 | Port-and-adapters with `.create()` factory and Protocol ports | Enables testability without mocks; consistent construction pattern across all adapters |
| Q3 2025 | No mocks — use fakes in `tests/fakes/` | Mocks couple tests to implementation; fakes exercise real logic and survive refactors |

## Review cadence

<!-- Pick a rhythm. Weekly is fine for active projects. The review is simple:
     1. Are the goals still honest and current?
     2. Is the task ordering still right?
     3. Did I drift this week? On what? -->

**Review every:** Every Monday @ 8PM
