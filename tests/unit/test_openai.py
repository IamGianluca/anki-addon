from addon.infrastructure.aqt import AddonConfig
from addon.infrastructure.openai import OpenAIClient


def test_llm_engine_collab():
    # Given
    expected = "ciao"
    config = AddonConfig.create_nullable()
    openai_client = OpenAIClient.create_null(config, [expected])
    prompt = "What is the Italian word for hello?"

    # When
    result = openai_client.run(prompt)

    # Then
    assert result == expected
