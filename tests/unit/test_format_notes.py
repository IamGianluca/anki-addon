import json
from anki.notes import Note

from addon.application.services.completion_service import (
    CompletionService,
    format_note_old,
)
from addon.application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from addon.infrastructure.aqt import AddonConfig
from addon.infrastructure.openai import OpenAIClient
from tests.fakes.aqt_fakes import FakeNote


def test_format_note_using_llm_old(note1):
    # Given
    config = AddonConfig.create_nullable()
    expected_front, expected_back = "front", "back"
    openai = OpenAIClient.create_nullable(
        config, responses=[expected_front, expected_back]
    )
    completion = CompletionService(openai)

    # When
    result = format_note_old(note1, completion)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back


def test_format_note_using_llm(note1):
    # Given
    config = AddonConfig.create_nullable()

    expected_front, expected_back = "Q1", "A1"
    response = json.dumps({"front": expected_front, "back": expected_back})
    openai = OpenAIClient.create_nullable(config, responses=[response])

    completion = CompletionService(openai)
    formatter = NoteFormatter(completion)

    # When
    result = format_note_workflow(note1, formatter)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back
