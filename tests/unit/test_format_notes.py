from anki.notes import Note

from addon.application.services.ai_completion_service import (
    CompletionService,
    format_note,
)
from addon.infrastructure.openai import AddonConfig, OpenAIClient
from tests.fakes.aqt_fakes import FakeNote


def test_ai_completion_service():
    # Given
    expected = "fake response"
    config = AddonConfig.create_nullable()
    openai = OpenAIClient.create_nullable(config, [expected])
    completion = CompletionService(openai)

    # When
    result = completion.generate_completion("fake prompt")

    # Then
    assert result.text == expected


def test_format_note_using_llm(note1):
    # Given
    expected_front, expected_back = "front", "back"
    config = AddonConfig.create_nullable()
    openai = OpenAIClient.create_nullable(
        config, responses=[expected_front, expected_back]
    )
    completion = CompletionService(openai)

    # When
    result = format_note(note1, completion)

    # Then
    assert isinstance(result, (Note, FakeNote))
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back
