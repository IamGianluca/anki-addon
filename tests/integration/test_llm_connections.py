import pytest

from addon.infrastructure.openai import LLMProviderConfig, OpenAIClient


@pytest.mark.slow
def test_openai():
    # Given
    config = LLMProviderConfig.create_nullable()
    openai_client = OpenAIClient.create(config)
    prompt = "What is the Italian word for hello?"

    # When
    result = openai_client.run(prompt)

    # Then
    assert result.strip().lower() == "ciao"
