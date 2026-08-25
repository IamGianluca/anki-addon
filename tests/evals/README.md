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
(`.envrc`). Select the provider with `LLM_PROVIDER` (`openai` default,
`opencode_go`):

- `openai`: `OPENAI_HOST`, `OPENAI_PORT`, `OPENAI_MODEL`, plus the
  optional `OPENAI_*` sampling/reasoning overrides.
- `opencode_go`: `OPENCODE_GO_API_KEY`, `OPENCODE_GO_MODEL`, plus the
  optional `OPENCODE_GO_TEMPERATURE` / `OPENCODE_GO_MAX_TOKENS`
  overrides.

The client is built through the same `create_completion_provider`
factory the addon uses, so an eval run measures the model, settings,
and provider wiring the addon actually ships with. Point the vars at a
different server/model to compare candidates on the same suite:

```bash
LLM_PROVIDER=opencode_go OPENCODE_GO_MODEL=glm-5.2 make eval
```

Every trial writes a full record (cluster, change set, transcript,
judge verdicts, grade) to `tests/evals/results/<timestamp>/`
(git-ignored). To summarize the latest run:

```bash
make eval_summary                                      # latest run
make eval_summary RESULTS=tests/evals/results/<stamp>  # older run
```

To keep a diffable history of scores, snapshot a run into the
tracked `tests/evals/scores.md` and commit it together with the
change it measures — the commit becomes the experiment record, and
diffing against the previous snapshot shows the effect line by line:

```bash
make eval_snapshot   # write tests/evals/scores.md from the latest run
```

The snapshot contains verdicts, failure details, and judge reasons.
Full transcripts and note content live in `results/` (git-ignored).

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
  applying the change set** (HTML stripped, case-insensitive, matched on
  word boundaries: `0.9` does not match `0.999`). Guards against
  rewrites that silently drop content.
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
separately — never silently counted either way.

The judge's instructions live in `judge_prompt.md` (edit it there);
the per-assertion rubric is each string in a task's `judge_assertions`.
**Every verdict — passes included — is recorded with its reason** in
the trial record under `judge_verdicts` and printed by `summarize.py`.
To review a decision, open the trial record: it contains the cluster
and the change set, i.e. everything the judge saw, so you can
re-adjudicate the assertion yourself. Two caveats:

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

## Production traces: the human as grader

The addon writes one JSON trace per curation session to
`<addon root>/traces/<timestamp>/note_<seed_id>.trial0.json` — the
same record shape the eval harness writes, so the viewer renders
both. The difference is the `outcome` field: in evals the graders
decide, in production the user decides in the review dialog
(`applied` / `rejected` / `cancelled` / `no_changes` / `failed`,
plus which proposals were approved vs rejected).

**A rejected or cancelled trace is a real failure** — a session where
the agent's proposals were not good enough. That makes production
traces the best source for new eval tasks: mine rejected sessions,
find the common failure mode, encode it as a task with a reference
solution, and you have a regression test for exactly what went wrong
in the field.

Reviewing traces (the addon writes them wherever Anki runs the
addon; copy them to the dev machine if needed):

```bash
make trace_viewer                    # or:
uv run python -m tests.evals.viewer --dir <addon-root>/traces
```

The production section of the dashboard lists sessions with their
outcome, model, and step count; each session page shows the
outcome (approved vs rejected proposals), the full transcript, and
an **annotation form** (label + notes) saved to `annotations.json`
next to the traces. The label field suggests labels already used,
so a consistent failure-mode taxonomy builds itself — when the same
label shows up on many sessions, turn it into an eval task.

The **Progress page** (link in the top bar) is where that taxonomy
surfaces: it shows review coverage per run (annotated / total) and
every failure mode grouped by label, with counts, the recorded
notes, and links back into the sessions. Agents working the loop
can read and update the mode descriptions through the JSON API:

```bash
curl -s http://127.0.0.1:5000/api/patterns                      # modes + coverage
curl -s -X POST http://127.0.0.1:5000/api/patterns \
  -H "Content-Type: application/json" \
  -d '{"did-not-split": {"description": "keeps compound notes intact"}}'
```

Counts and example records are always derived from `annotations.json`;
the taxonomy (stored in `patterns.json` next to the run folders) holds
only the agent's descriptions, so interpretation and evidence cannot
disagree. The Progress page shows both side by side.

Eval trial pages have the same annotation form, useful for marking
unfair failures while reading transcripts.

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
