from addon.application.services.ai_service import AICompletionService
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
