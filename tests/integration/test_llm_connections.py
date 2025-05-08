import pytest

from addon.llm import OpenAIClient


@pytest.mark.slow
def test_openai():
    # Given
    openai_client = OpenAIClient.create()
    prompt = "What is the Italian word for hello?"

    # When
    result = openai_client.run(prompt)

    # Then
    assert result.strip().lower() == "ciao"
