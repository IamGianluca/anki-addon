"""LLM-free tests for the viewer's failure-mode aggregation."""

from __future__ import annotations

from tests.evals.viewer import (
    RunSummary,
    coverage,
    failure_modes,
    load_patterns,
    parse_annotation_key,
    save_patterns,
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

    # Then
    assert list(modes) == ["alpha", "beta", "zebra"]


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
