from addon.application.services.completion_service import (
    CompletionService,
)
from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient


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
