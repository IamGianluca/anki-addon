import json

from anki.notes import Note
from tests.fakes.aqt_fakes import FakeNote

from addon.application.services.completion_service import (
    CompletionService,
)
from addon.application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient
from addon.utils import is_cloze_note


def test_format_note_using_llm(note1):
    # Given
    config = AddonConfig.create_nullable()

    expected_front, expected_back = "Q1", "A1"
    response = json.dumps({"front": expected_front, "back": expected_back})
    openai = OpenAIClient.create_null(config, responses=[response])

    completion = CompletionService(openai)
    formatter = NoteFormatter(completion)

    # When
    result = format_note_workflow(note1, formatter)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back
    assert not is_cloze_note(result)


def test_format_cloze_note_using_llm(cloze1):
    # Given
    config = AddonConfig.create_nullable()

    expected_front, expected_back = "This is a {{c1::fake note}}", ""
    response = json.dumps({"front": expected_front, "back": expected_back})
    openai = OpenAIClient.create_null(config, responses=[response])

    completion = CompletionService(openai)
    formatter = NoteFormatter(completion)

    # When
    result = format_note_workflow(cloze1, formatter)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Text"] == expected_front
    assert result["Back Extra"] == expected_back
    assert is_cloze_note(result)
