# Capability evals for the CuratorAgent

An LLM-in-the-loop eval harness for the curation agent. Each task seeds
a fresh in-memory `FakeNoteRepository`, runs the **real** `CuratorAgent`
with a real LLM client against it, and grades the resulting
`ProposedChangeSet` (the outcome) plus rule adherence visible in the
transcript. No eval ever touches a real Anki collection.

Two kinds of tasks:

- **capability** — "what can the agent do well?" A capability suite
  should start with a low pass rate: it gives prompt and model changes
  a hill to climb. These report but never fail the build.
- **regression** — "does it still do what it used to?" These must pass
  every trial; a drop means something broke. Promote a capability task
  to regression once it passes reliably.

## Running

Evals are opt-in: they are slow, non-deterministic, and spend LLM
tokens, so they are skipped in `make test` / `make test_slow`.

```bash
make eval                                # report-only
EVAL_STRICT=1 make eval                  # capability failures fail too
RUN_EVALS=1 uv run pytest tests/evals/ -k split   # run a subset
```

The LLM is configured from the same env vars as the integration tests
(`.envrc`): `OPENAI_HOST`, `OPENAI_PORT`, `OPENAI_MODEL`, plus the
optional `OPENAI_*` sampling/reasoning overrides — an eval run measures
the model and settings the addon actually ships with. Point the vars at
a different server/model to compare candidates on the same suite.

Every trial writes a full record (cluster, change set, transcript,
grade) to `tests/evals/results/<timestamp>/` (git-ignored). To
summarize a run:

```bash
uv run python tests/evals/summarize.py tests/evals/results/<stamp>
```

**Read the transcripts when a task fails.** A failure should look fair:
it should be obvious what went wrong and why. If the agent found a
valid solution the graders rejected, fix the grader or the task — not
the score.

## Trials and metrics

`trials` sets how often a task runs per eval invocation (default 1;
raise to 3–5 for tasks you rely on). One run proves little, so report:

- **pass@1** — mean per-trial success rate.
- **pass^k** — all k trials passed. The number that matters here:
  proposals get applied to a real collection after review, so
  reliability every time is the product requirement. At 75% per-trial
  success, pass^3 is only ~42%.

## Task files

One JSON file per task in `tasks/`. See the existing files for examples.

| field | meaning |
|---|---|
| `id` | unique task id (used in record filenames) |
| `suite` | `"capability"` (report-only) or `"regression"` (must pass^k) |
| `desc` | what the task tests; shown to the LLM judge for context |
| `seed_note_id` | note the agent starts from |
| `instruction` | optional free-text instruction to the agent |
| `trials` | k, default 1 |
| `max_steps` | agent loop cap, default 15 |
| `notes` | seeded cluster: `id`, `front`, `back`, `tags`, `notetype`, `extra_fields` |
| `expect` | deterministic success criteria (below) |
| `judge_assertions` | LLM-judge assertions, one call each |
| `reference` | human-authored proposals that pass the outcome graders |

### Deterministic graders (`expect`)

- `finish` (default true) — the agent ended with `finish`, not max_steps.
- `empty` — no proposals. The should-not-fire guard.
- `edits` / `creates` / `deletes` — `[min, max]` proposal counts.
  A split counts as one edit + its creates.
- `must_touch` / `must_not_touch` — note ids that must / must not
  appear in an edit or delete proposal.
- `facts` — strings that must appear somewhere in the notes **after
  applying the change set** (HTML stripped, case-insensitive). Guards
  against rewrites that silently drop content.
- `read_before_propose` (default true) — every edit/split/delete of a
  note other than the seed must be preceded by reading it. Enforces a
  rule from the agent's own system prompt; the seed is exempt because
  its content is already in the first prompt.
- Cloze preservation is automatic: an edit to a cloze note must keep
  `{{cN::...}}` markup in the front.

### LLM judge (`judge_assertions`)

Each assertion is judged in a **separate** call (no trading dimensions
off against each other), seeing the cluster, the change set, and one
assertion, answering `pass` / `fail` / `unknown`. `unknown` is recorded
separately — never silently counted either way. Two caveats:

- The judge is the same client (and model) as the agent by default,
  which means self-grading bias. For calibration runs, point the env
  vars at a stronger model.
- Calibrate new assertions before trusting them: run a handful of
  trials and check the judge's verdicts against your own reading of
  the transcripts.

### Reference solutions

Every task needs a `reference` (for `empty` tasks the reference *is*
the empty change set). `test_task_files.py` — fast, LLM-free, runs in
`make test_slow` — verifies each reference passes the outcome graders.
It proves the task is solvable and the graders are wired correctly; a
0% pass rate on a task whose reference validates usually means a hard
task, but re-read the spec before blaming the model.

## Writing good tasks

- **Mine real failures**: proposals you rejected in review, notes the
  agent mangled. Invented tasks measure what you imagined, not what
  happens.
- **Unambiguous success criteria**: two people reading the task should
  reach the same pass/fail verdict. Everything the graders check must
  be discoverable from the note content and the agent's system prompt.
- **Balance the set**: for every "should change" task keep a "should
  leave alone" task. One-sided suites produce over-eager agents.
- **Grade outcomes, not paths**: the agent may merge duplicates in
  either direction, search in any order. Encode what the cluster must
  look like, not the steps to get there.

The same harness pattern — real client, fake note repository, outcome
grading — extends to the single-turn `NoteFormatter` when its prompt
or model needs evaluating.
