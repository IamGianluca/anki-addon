import json

from tests.fakes.openai_fakes import FakeCompletionProvider

from addon.application.services.formatter_service import NoteFormatter
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
