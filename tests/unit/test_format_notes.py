import json

from anki.notes import Note
from tests.fakes.aqt_fakes import FakeNote

from addon.application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from addon.infrastructure.external_services.openai import OpenAIClient
from addon.utils import is_cloze_note


def test_format_note_using_llm(addon_config, note1):
    # Given
    expected_front, expected_back = "Q1", "A1"
    response = json.dumps({"front": expected_front, "back": expected_back})
    openai = OpenAIClient.create_null(addon_config, responses=[response])

    formatter = NoteFormatter(openai)

    # When
    result = format_note_workflow(note1, formatter)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back
    assert not is_cloze_note(result)


def test_format_cloze_note_using_llm(addon_config, cloze1):
    # Given
    expected_front, expected_back = "This is a {{c1::fake note}}", ""
    response = json.dumps({"front": expected_front, "back": expected_back})
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When
    result = format_note_workflow(cloze1, formatter)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Text"] == expected_front
    assert result["Back Extra"] == expected_back
    assert is_cloze_note(result)


def test_format_note_preserves_tags(addon_config, note1):
    # Given
    note1.tags = ["original", "tags"]
    response = json.dumps({"front": "Q", "back": "A", "tags": ["new", "tags"]})
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When
    result = format_note_workflow(note1, formatter)

    # Then - tags should NOT be updated (per comment in formatter_service.py:73)
    assert result.tags == ["original", "tags"]


def test_format_note_handles_html_br_tags(addon_config, note1):
    # Given
    note1["Front"] = "Line 1<br>Line 2"
    note1["Back"] = "Answer"
    response = json.dumps({"front": "Formatted<br>Text", "back": "A"})
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When
    result = format_note_workflow(note1, formatter)

    # Then
    assert "Formatted<br>Text" in result["Front"]


def test_format_note_removes_alt_tags_from_images(addon_config, note1):
    # Given
    response = json.dumps(
        {"front": '<img alt="test" src="foo.jpg">', "back": "A"}
    )
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When
    result = format_note_workflow(note1, formatter)

    # Then
    assert "alt=" not in result["Front"]
    assert "<img " in result["Front"]
