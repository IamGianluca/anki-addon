"""Unit tests for the deterministic outcome graders.

LLM-free, like test_task_files: tasks are constructed in code and
graded without proposals, so the final cluster state is the seeded
state. Runs in make test_slow.
"""

from tests.evals.graders import GradeResult, grade_outcome
from tests.evals.harness import EvalTask, Expectation, TaskNote


def _grade_facts(backs: list[str], facts: list[str]) -> GradeResult:
    """Grade a seeded cluster as-is (no proposals) for the given facts."""
    task = EvalTask(
        id="fact_boundaries",
        desc="fact matching semantics",
        seed_note_id=1,
        notes=[
            TaskNote(id=i + 1, front=f"Q{i + 1}?", back=back)
            for i, back in enumerate(backs)
        ],
        expect=Expectation(facts=facts),
    )
    return grade_outcome(task, [])


def _verdict(result: GradeResult, fact: str) -> str:
    return next(c for c in result.checks if c.name == f"fact_{fact}").verdict


def test_fact_does_not_match_inside_a_longer_number():
    # Given a cluster whose only value is the overlapping "0.999"
    # When it is graded for the fact "0.9"
    result = _grade_facts(["0.999."], ["0.9"])

    # Then the fact is reported missing — plain substring matching
    # used to pass this vacuously ("0.9" is a substring of "0.999")
    assert _verdict(result, "0.9") == "fail"


def test_fact_matches_as_a_standalone_token():
    # Given a note carrying the value as its own token
    # When it is graded for that value
    result = _grade_facts(["0.9."], ["0.9"])

    # Then the check passes
    assert _verdict(result, "0.9") == "pass"


def test_overlapping_facts_are_checked_independently():
    # Given a cluster carrying both overlapping values (the
    # split_compound reference outcome)
    # When it is graded for both facts
    result = _grade_facts(["0.9.", "0.999."], ["0.9", "0.999"])

    # Then both pass — the boundary rule must not overcorrect
    assert _verdict(result, "0.9") == "pass"
    assert _verdict(result, "0.999") == "pass"


def test_fact_does_not_match_inside_a_longer_word():
    # Given a note that mentions "length" but never the len() fact
    # When it is graded for the fact "len"
    result = _grade_facts(["Returns the length of an object."], ["len"])

    # Then the fact is reported missing
    assert _verdict(result, "len") == "fail"


def test_fact_matches_across_punctuation():
    # Given a note carrying the term glued to punctuation
    # When it is graded for the bare term
    result = _grade_facts(
        ["len() returns the number of items in an object."], ["len"]
    )

    # Then the check passes — boundaries are word characters, not spaces
    assert _verdict(result, "len") == "pass"
