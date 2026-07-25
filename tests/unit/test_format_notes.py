import json

from tests.fakes.aqt_fakes import FakeNote
from tests.fakes.openai_fakes import FakeCompletionProvider

from addon.application.services.formatter_service import (
    AnkiNoteMapper,
    NoteFormatter,
)
from addon.domain.entities.note import AddonNote, AddonNoteType


def test_format_note_using_llm(addon_note1: AddonNote) -> None:
    # Given
    expected_front, expected_back = "Q1", "A1"
    response = json.dumps({"front": expected_front, "back": expected_back})
    fake_llm = FakeCompletionProvider([response])
    formatter = NoteFormatter(fake_llm)

    # When
    result = formatter.format(addon_note1)

    # Then
    assert isinstance(result, AddonNote)
    assert result.front == expected_front
    assert result.back == expected_back
    assert result.notetype == AddonNoteType.BASIC


def test_format_cloze_note_using_llm(addon_cloze_note1: AddonNote) -> None:
    # Given
    expected_front, expected_back = "This is a {{c1::fake note}}", ""
    response = json.dumps({"front": expected_front, "back": expected_back})
    fake_llm = FakeCompletionProvider([response])
    formatter = NoteFormatter(fake_llm)

    # When
    result = formatter.format(addon_cloze_note1)

    # Then
    assert isinstance(result, AddonNote)
    assert result.front == expected_front
    assert result.back == expected_back
    assert result.notetype == AddonNoteType.CLOZE


def test_format_note_preserves_tags(addon_note1: AddonNote) -> None:
    # Given
    addon_note1.tags = ["original", "tags"]
    response = json.dumps({"front": "Q", "back": "A", "tags": ["new", "tags"]})
    fake_llm = FakeCompletionProvider([response])
    formatter = NoteFormatter(fake_llm)

    # When
    result = formatter.format(addon_note1)

    # Then - tags should NOT be updated
    assert result.tags == ["original", "tags"]


def test_format_note_handles_html_br_tags(addon_note1: AddonNote) -> None:
    # Given
    addon_note1.front = "Line 1<br>Line 2"
    addon_note1.back = "Answer"
    response = json.dumps({"front": "Formatted<br>Text", "back": "A"})
    fake_llm = FakeCompletionProvider([response])
    formatter = NoteFormatter(fake_llm)

    # When
    result = formatter.format(addon_note1)

    # Then
    assert "Formatted<br>Text" in result.front


def test_format_note_removes_alt_tags_from_images(
    addon_note1: AddonNote,
) -> None:
    # Given
    response = json.dumps(
        {"front": '<img alt="test" src="foo.jpg">', "back": "A"}
    )
    fake_llm = FakeCompletionProvider([response])
    formatter = NoteFormatter(fake_llm)

    # When
    result = formatter.format(addon_note1)

    # Then
    assert "alt=" not in result.front
    assert "<img " in result.front


def test_mapper_captures_fields_beyond_front_and_back() -> None:
    # Given
    anki_note = FakeNote(
        1,
        {"Front": "Q", "Back": "A", "Extra": "an example", "Difficulty": "2"},
    )

    # When
    addon_note = AnkiNoteMapper.to_addon_note(anki_note)

    # Then
    assert addon_note.extra_fields == {
        "Extra": "an example",
        "Difficulty": "2",
    }


def test_mapper_of_standard_notetype_has_no_extra_fields() -> None:
    # Given
    anki_note = FakeNote(1, {"Front": "Q", "Back": "A"})

    # When
    addon_note = AnkiNoteMapper.to_addon_note(anki_note)

    # Then
    assert addon_note.extra_fields == {}


def test_merge_writes_back_extra_fields() -> None:
    # Given
    anki_note = FakeNote(
        1, {"Front": "Q", "Back": "A", "Extra": "old", "Difficulty": "2"}
    )
    addon_note = AnkiNoteMapper.to_addon_note(anki_note)
    addon_note.extra_fields["Extra"] = "new example"

    # When
    AnkiNoteMapper.merge_addon_changes(anki_note, addon_note)

    # Then
    assert anki_note["Extra"] == "new example"
    assert anki_note["Difficulty"] == "2"


def test_merge_skips_extra_fields_the_notetype_does_not_have() -> None:
    # Given
    anki_note = FakeNote(1, {"Front": "Q", "Back": "A"})
    addon_note = AddonNote(
        front="Q", back="A", extra_fields={"Extra": "ignored"}
    )

    # When
    AnkiNoteMapper.merge_addon_changes(anki_note, addon_note)

    # Then
    assert "Extra" not in anki_note.keys()
