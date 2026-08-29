"""LLM-free tests for the production review batch sampler."""

from __future__ import annotations

import json

from tests.evals.sample_batch import load_annotated, select_batch


def _write_trace(
    traces_dir,
    stamp: str,
    task_id: str,
    *,
    change_set=None,
    steps: int = 4,
    outcome: str = "applied",
    trial: int = 0,
) -> None:
    """A minimal production trace: just the fields the sampler reads."""
    run_dir = traces_dir / stamp
    run_dir.mkdir(exist_ok=True)
    record = {
        "task_id": task_id,
        "trial": trial,
        "outcome": {"status": outcome},
        "change_set": change_set or [],
        "transcript": [{}] * steps,
    }
    (run_dir / f"{task_id}.trial{trial}.json").write_text(
        json.dumps(record), encoding="utf-8"
    )


def _annotate(
    traces_dir, stamp: str, task_id: str, label: str = "pass"
) -> None:
    ann = traces_dir / stamp / "annotations.json"
    data = json.loads(ann.read_text(encoding="utf-8")) if ann.exists() else {}
    data[f"{task_id}.trial0.json"] = {"label": label, "note": "ok"}
    ann.write_text(json.dumps(data), encoding="utf-8")


def test_batch_excludes_annotated_records_in_any_run(tmp_path):
    # Given a trace annotated in its own run, and one annotated
    # in an unrelated run
    _write_trace(tmp_path, "20260101T000000Z", "note_1", outcome="applied")
    _annotate(tmp_path, "20260101T000000Z", "note_1")
    _write_trace(tmp_path, "20260102T000000Z", "note_2", outcome="applied")
    _annotate(tmp_path, "20260102T000000Z", "note_2")
    _write_trace(tmp_path, "20260103T000000Z", "note_3", outcome="no_changes")

    # When selecting a batch
    batch = select_batch(tmp_path, size=10)

    # Then only the never-annotated note is suggested
    assert [e["task_id"] for e in batch] == ["note_3"]


def test_batch_keeps_most_informative_run_per_note(tmp_path):
    # Given two runs of the same note, one proposing changes
    _write_trace(
        tmp_path,
        "20260101T000000Z",
        "note_1",
        change_set=[{"type": "edit"}],
        steps=2,
        outcome="applied",
    )
    _write_trace(
        tmp_path,
        "20260102T000000Z",
        "note_1",
        change_set=[],
        steps=12,
        outcome="no_changes",
    )

    # When selecting a batch
    batch = select_batch(tmp_path, size=10)

    # Then the run that proposed changes wins over the longer idle one
    assert len(batch) == 1
    assert batch[0]["run"] == "20260101T000000Z"
    assert "edit" in batch[0]["reason"]


def test_batch_round_robins_across_outcome_statuses(tmp_path):
    # Given three unannotated notes, one per outcome status
    for i, status in enumerate(("applied", "rejected", "no_changes")):
        _write_trace(
            tmp_path, f"2026010{i + 1}T000000Z", f"note_{i}", outcome=status
        )

    # When selecting a batch of one
    batch = select_batch(tmp_path, size=1)

    # Then the single slot goes to the first status in round-robin order
    # (deterministic task_id order), and larger batches mix statuses
    assert [e["task_id"] for e in select_batch(tmp_path, size=3)] == [
        "note_0",
        "note_1",
        "note_2",
    ]
    assert len(batch) == 1


def test_batch_respects_size_limit(tmp_path):
    # Given more eligible notes than the requested batch size
    for i in range(5):
        _write_trace(tmp_path, f"2026010{i + 1}T000000Z", f"note_{i}")

    # When selecting a batch of three
    batch = select_batch(tmp_path, size=3)

    # Then exactly three entries come back
    assert len(batch) == 3
    assert len({e["task_id"] for e in batch}) == 3


def test_load_annotated_collects_names_across_runs(tmp_path):
    # Given annotations in two separate run directories
    _write_trace(tmp_path, "20260101T000000Z", "note_1")
    _annotate(tmp_path, "20260101T000000Z", "note_1")
    _write_trace(tmp_path, "20260102T000000Z", "note_2")
    _annotate(tmp_path, "20260102T000000Z", "note_2")

    # When loading the annotated set
    names, note_ids = load_annotated(tmp_path)

    # Then both records and both note ids are known
    assert names == {"note_1.trial0.json", "note_2.trial0.json"}
    assert note_ids == {"note_1", "note_2"}
