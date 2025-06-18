from addon.application.services.completion_service import (
    CompletionService,
)
from addon.infrastructure.aqt import AddonConfig
from addon.infrastructure.openai import OpenAIClient


def test_completion_service():
    # Given
    expected = "fake response"
    config = AddonConfig.create_nullable()
    openai = OpenAIClient.create_null(config, [expected])
    completion = CompletionService(openai)

    # When
    result = completion.generate("fake prompt")

    # Then
    assert result.text == expected
