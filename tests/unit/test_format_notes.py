from addon.application.services.ai_completion_service import (
    AICompletionService,
    format_note_using_llm,
)
from addon.infrastructure.openai import OpenAIClient


def test_ai_completion_service():
    # Given
    expected = "fake response"
    openai = OpenAIClient.create_nullable([expected])
    completion = AICompletionService(openai)

    # When
    result = completion.generate_completion("fake prompt")

    # Then
    assert result.text == expected


def test_format_note_using_llm(note1):
    # Given
    expected_front, expected_back = "front", "back"
    openai = OpenAIClient.create_nullable(
        responses=[expected_front, expected_back]
    )
    completion = AICompletionService(openai)

    # When
    result = format_note_using_llm(note1, completion)

    # Then
    assert result["Front"] == expected_front
    assert result["Back"] == expected_back
