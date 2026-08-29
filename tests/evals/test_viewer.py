"""LLM-free tests for the viewer's failure-mode aggregation."""

from __future__ import annotations

from tests.evals.viewer import (
    RunSummary,
    TrialRecord,
    _failure_mode_cards,
    batch_items,
    coverage,
    failure_modes,
    load_batch,
    load_patterns,
    mode_status,
    next_batch_item,
    parse_annotation_key,
    save_batch,
    save_patterns,
    set_resolved,
)


def _run(
    stamp: str,
    *,
    total_trials: int,
    annotations: dict | None = None,
) -> RunSummary:
    """A run with just the fields aggregation reads."""
    return RunSummary(
        stamp=stamp,
        total_trials=total_trials,
        annotations=annotations or {},
    )


def _trial(
    task_id: str,
    trial_index: int = 0,
    *,
    outcome: dict | None = None,
    summary: str = "",
) -> TrialRecord:
    """A production trial with just the fields the batch reads."""
    return TrialRecord(
        task_id=task_id,
        trial_index=trial_index,
        passed=True,
        score=1.0,
        checks=[],
        judge_verdicts=[],
        stats={},
        summary=summary,
        cluster=[],
        change_set=[],
        transcript=[],
        model="test-model",
        source="production",
        outcome=outcome,
        file_name=f"{task_id}.trial{trial_index}.json",
    )


def _prod_run(
    stamp: str, *trials: TrialRecord, annotations: dict | None = None
) -> RunSummary:
    tasks: dict[str, list[TrialRecord]] = {}
    for t in trials:
        tasks.setdefault(t.task_id, []).append(t)
    return RunSummary(
        stamp=stamp,
        total_trials=len(trials),
        tasks=tasks,
        annotations=annotations or {},
        is_production=True,
    )


def test_failure_modes_groups_annotations_by_label() -> None:
    # Given
    runs = [
        _run(
            "20260811T130055Z",
            total_trials=2,
            annotations={
                "note_1.trial0.json": {
                    "label": "did-not-split",
                    "note": "kept compound note intact",
                },
                "note_2.trial1.json": {
                    "label": "full-stop",
                    "note": "trailing period in back",
                },
            },
        ),
        _run(
            "20260811T130948Z",
            total_trials=1,
            annotations={
                "note_3.trial0.json": {
                    "label": "did-not-split",
                    "note": "deleted a note instead of splitting",
                }
            },
        ),
    ]

    # When
    modes = failure_modes(runs)

    # Then
    assert set(modes) == {"did-not-split", "full-stop"}
    assert modes["did-not-split"]["count"] == 2
    assert modes["full-stop"]["count"] == 1
    # Records are sorted newest run first.
    assert [r["task_id"] for r in modes["did-not-split"]["records"]] == [
        "note_3",
        "note_1",
    ]
    assert modes["full-stop"]["records"][0]["run"] == ("20260811T130055Z")
    assert modes["full-stop"]["records"][0]["note"] == (
        "trailing period in back"
    )


def test_failure_modes_skips_unlabelled_and_unparseable_keys() -> None:
    # Given
    runs = [
        _run(
            "runA",
            total_trials=1,
            annotations={
                "note_1.trial0.json": {"label": "", "note": "unlabelled"},
                "notes.txt": {"label": "junk", "note": "bad key"},
                "note_2.trial0.json": {"label": "real", "note": "counts"},
            },
        )
    ]

    # When
    modes = failure_modes(runs)

    # Then
    assert set(modes) == {"real"}
    assert modes["real"]["count"] == 1


def test_failure_modes_excludes_pass_labels_but_coverage_counts_them() -> None:
    # Given
    annotations = {
        "note_1.trial0.json": {"label": "pass", "note": "LGTM"},
        "note_2.trial0.json": {
            "label": "did-not-follow-instructions",
            "note": "used 'you'",
        },
    }
    runs = [_run("runA", total_trials=2, annotations=annotations)]

    # When
    modes = failure_modes(runs)
    stats = coverage(runs)

    # Then
    assert set(modes) == {"did-not-follow-instructions"}
    assert stats["annotated"] == 2  # the pass still counts as reviewed


def test_failure_modes_sorts_by_count_then_label() -> None:
    # Given
    runs = [
        _run(
            "runA",
            total_trials=4,
            annotations={
                "a.trial0.json": {"label": "zebra"},
                "b.trial0.json": {"label": "beta"},
                "c.trial0.json": {"label": "alpha"},
                "d.trial0.json": {"label": "alpha"},
            },
        )
    ]

    # When
    modes = failure_modes(runs)

    # Then — same recency, so count desc then label asc
    assert list(modes) == ["alpha", "beta", "zebra"]


def test_failure_modes_derives_recency_from_run_stamps() -> None:
    # Given — the mode in every run of a six-run corpus
    runs = [
        _run(
            f"run{i:02d}",
            total_trials=1,
            annotations={f"a{i}.trial0.json": {"label": "old"}},
        )
        for i in range(6)
    ]

    # When — two newest runs count as recent
    modes = failure_modes(runs, active_window=2)

    # Then
    assert modes["old"]["count"] == 6
    assert modes["old"]["active_count"] == 2
    assert modes["old"]["last_seen"] == "run05"


def test_failure_modes_sorts_by_last_seen_not_count() -> None:
    # Given — a frequent mode last seen in an old run, a rare one in
    # the newest run
    runs = [
        _run(
            "runA",
            total_trials=4,
            annotations={
                f"a{i}.trial0.json": {"label": "frequent-old"}
                for i in range(4)
            },
        ),
        _run(
            "runB",
            total_trials=1,
            annotations={"b.trial0.json": {"label": "rare-new"}},
        ),
    ]

    # When — only the newest run is active
    modes = failure_modes(runs, active_window=1)

    # Then — recency wins over cumulative count
    assert list(modes) == ["rare-new", "frequent-old"]
    assert modes["frequent-old"]["active_count"] == 0
    assert modes["rare-new"]["active_count"] == 1


def test_mode_status_combines_recency_and_resolution() -> None:
    # Given / When / Then
    assert mode_status({"active_count": 2}, "") == "active"
    assert mode_status({"active_count": 0}, "") == "quiet"
    assert (
        mode_status({"active_count": 0}, "2026-08-12 10:00 UTC") == "resolved"
    )
    # Occurrence data wins over the stored flag.
    assert (
        mode_status({"active_count": 1}, "2026-08-12 10:00 UTC") == "recurred"
    )


def test_set_resolved_keeps_description_and_toggles_flag() -> None:
    # Given
    patterns = {"m": {"description": "keeps compound notes intact"}}

    # When — marking resolved
    set_resolved(patterns, "m", True)

    # Then
    assert patterns["m"]["description"] == "keeps compound notes intact"
    assert "resolved_at" in patterns["m"]

    # When — reopening clears the flag but keeps the description
    set_resolved(patterns, "m", False)

    # Then
    assert patterns["m"] == {"description": "keeps compound notes intact"}


def test_failure_mode_cards_bucket_by_status() -> None:
    # Given — one mode per status; recurred and resolved carry the flag
    modes = {
        "active-mode": {
            "count": 2,
            "active_count": 2,
            "last_seen": "runC",
            "records": [],
        },
        "recurred-mode": {
            "count": 1,
            "active_count": 1,
            "last_seen": "runB",
            "records": [],
        },
        "quiet-mode": {
            "count": 1,
            "active_count": 0,
            "last_seen": "runA",
            "records": [],
        },
        "resolved-mode": {
            "count": 1,
            "active_count": 0,
            "last_seen": "runA",
            "records": [],
        },
    }
    stored = {
        "recurred-mode": {
            "description": "came back",
            "resolved_at": "2026-08-01 10:00 UTC",
        },
        "resolved-mode": {
            "description": "done",
            "resolved_at": "2026-08-01 10:00 UTC",
        },
    }

    # When
    active, dormant, resolved = _failure_mode_cards(modes, stored)

    # Then — recurred joins the active surface, resolved stays collapsed
    assert len(active) == 2
    assert len(dormant) == 1
    assert len(resolved) == 1


def test_parse_annotation_key_splits_task_and_trial() -> None:
    # Given / When
    parsed = parse_annotation_key("note_1644077469037.trial0.json")

    # Then
    assert parsed == ("note_1644077469037", 0)


def test_parse_annotation_key_rejects_other_names() -> None:
    # Given / When
    parsed = parse_annotation_key("annotations.json")

    # Then
    assert parsed is None


def test_coverage_counts_annotations_and_trials_per_run() -> None:
    # Given
    runs = [
        _run(
            "runA",
            total_trials=5,
            annotations={"a.trial0.json": {"label": "x"}},
        ),
        _run("runB", total_trials=3),
    ]

    # When
    stats = coverage(runs)

    # Then
    assert stats["annotated"] == 1
    assert stats["total"] == 8
    assert stats["per_run"] == {
        "runA": {"annotated": 1, "total": 5},
        "runB": {"annotated": 0, "total": 3},
    }


def test_patterns_round_trip_to_disk(tmp_path) -> None:
    # Given
    path = tmp_path / "patterns.json"
    taxonomy = {
        "did-not-split": {"description": "keeps compound notes intact"}
    }

    # When
    save_patterns(taxonomy, path)
    loaded = load_patterns(path)

    # Then
    assert loaded == taxonomy


def test_load_patterns_absent_file_is_empty(tmp_path) -> None:
    # Given / When
    loaded = load_patterns(tmp_path / "missing.json")

    # Then
    assert loaded == {}


# ---------------------------------------------------------------------------
# Review batch
# ---------------------------------------------------------------------------


def test_batch_items_enriches_entries_in_order() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial(
                "note_1", outcome={"status": "rejected"}, summary="bad edit"
            ),
        ),
        _prod_run(
            "runB",
            _trial("note_2", outcome={"status": "no_changes"}),
        ),
    ]
    batch = [
        {
            "run": "runB",
            "task_id": "note_2",
            "trial": 0,
            "reason": "no_changes probe",
        },
        {"run": "runA", "task_id": "note_1", "trial": 0},
    ]

    # When
    items = batch_items(batch, runs)

    # Then
    assert [i["run"] for i in items] == ["runB", "runA"]
    assert items[0]["outcome"] == "no_changes"
    assert items[0]["reason"] == "no_changes probe"
    assert items[1]["outcome"] == "rejected"
    assert items[1]["summary"] == "bad edit"


def test_batch_items_skips_stale_and_duplicate_entries() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1", outcome={"status": "failed"}),
        )
    ]
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},
        {"run": "runA", "task_id": "note_1", "trial": 0},  # duplicate
        {"run": "runA", "task_id": "note_1", "trial": 1},  # no such trial
        {"run": "runA", "task_id": "ghost", "trial": 0},  # no such task
        {"run": "nope", "task_id": "note_1", "trial": 0},  # no such run
    ]

    # When
    items = batch_items(batch, runs)

    # Then
    assert len(items) == 1
    assert items[0]["outcome"] == "failed"


def test_batch_items_attaches_annotation_label() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1"),
            annotations={
                "note_1.trial0.json": {"label": "did-not-split", "note": "x"}
            },
        )
    ]

    # When
    items = batch_items(
        [{"run": "runA", "task_id": "note_1", "trial": 0}], runs
    )

    # Then
    assert items[0]["label"] == "did-not-split"
    assert items[0]["annotated"] is True


def test_batch_items_sorts_annotated_to_bottom() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1"),
            annotations={"note_1.trial0.json": {"label": "x", "note": ""}},
        ),
        _prod_run(
            "runB",
            _trial("note_2"),
            annotations={},
        ),
        _prod_run(
            "runC",
            _trial("note_3"),
            annotations={"note_3.trial0.json": {"note": "no label"}},
        ),
    ]
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},  # annotated
        {"run": "runB", "task_id": "note_2", "trial": 0},  # unannotated
        {"run": "runC", "task_id": "note_3", "trial": 0},  # note only
    ]

    # When
    items = batch_items(batch, runs)

    # Then
    assert [i["annotated"] for i in items] == [False, True, True]
    assert [i["run"] for i in items] == ["runB", "runA", "runC"]


def test_next_batch_item_advances_past_annotated_entries() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1"),
            annotations={"note_1.trial0.json": {"label": "x"}},
        ),
        _prod_run("runB", _trial("note_2")),
    ]
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},
        {"run": "runB", "task_id": "note_2", "trial": 0},
    ]

    # When — reviewing the annotated session should skip it
    nxt = next_batch_item(batch, "runA", "note_1", 0, runs)

    # Then
    assert nxt["task_id"] == "note_2"


def test_next_batch_item_wraps_around_to_first_unannotated() -> None:
    # Given
    runs = [
        _prod_run("runA", _trial("note_1")),
        _prod_run("runB", _trial("note_2")),
        _prod_run(
            "runC",
            _trial("note_3"),
            annotations={"note_3.trial0.json": {"label": "x"}},
        ),
    ]
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},
        {"run": "runB", "task_id": "note_2", "trial": 0},
        {"run": "runC", "task_id": "note_3", "trial": 0},
    ]

    # When — current is the middle entry; the only unannotated after
    # it is none, so wrap back to the first entry
    nxt = next_batch_item(batch, "runB", "note_2", 0, runs)

    # Then
    assert nxt["task_id"] == "note_1"


def test_next_batch_item_none_when_current_is_last_unannotated() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1"),
            annotations={"note_1.trial0.json": {"label": "x"}},
        ),
        _prod_run("runB", _trial("note_2")),
    ]
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},
        {"run": "runB", "task_id": "note_2", "trial": 0},
    ]

    # When — the only unannotated entry left is the current session
    nxt = next_batch_item(batch, "runB", "note_2", 0, runs)

    # Then
    assert nxt is None


def test_next_batch_item_from_not_in_batch_picks_first() -> None:
    # Given
    runs = [_prod_run("runA", _trial("note_1"))]
    batch = [{"run": "runA", "task_id": "note_1", "trial": 0}]

    # When — session not in the batch at all
    nxt = next_batch_item(batch, "other", "note_9", 0, runs)

    # Then
    assert nxt["task_id"] == "note_1"


def test_next_batch_item_none_when_all_annotated() -> None:
    # Given
    runs = [
        _prod_run(
            "runA",
            _trial("note_1"),
            annotations={"note_1.trial0.json": {"label": "x"}},
        )
    ]
    batch = [{"run": "runA", "task_id": "note_1", "trial": 0}]

    # When
    nxt = next_batch_item(batch, "runA", "note_1", 0, runs)

    # Then
    assert nxt is None


def test_batch_round_trip_to_disk(tmp_path) -> None:
    # Given
    path = tmp_path / "batch.json"
    batch = [{"run": "runA", "task_id": "note_1", "trial": 0, "reason": "x"}]

    # When
    save_batch(batch, path)
    loaded = load_batch(path)

    # Then
    assert loaded == batch


def test_save_batch_drops_malformed_entries(tmp_path) -> None:
    # Given
    path = tmp_path / "batch.json"
    batch = [
        {"run": "runA", "task_id": "note_1", "trial": 0},
        {"run": "runA", "task_id": "note_1", "trial": "0"},  # string trial
        {"run": "runA"},  # missing fields
        "junk",  # not a dict
    ]

    # When
    save_batch(batch, path)

    # Then
    assert load_batch(path) == [
        {"run": "runA", "task_id": "note_1", "trial": 0}
    ]


def test_load_batch_absent_file_is_empty(tmp_path) -> None:
    # Given / When
    loaded = load_batch(tmp_path / "missing.json")

    # Then
    assert loaded == []
