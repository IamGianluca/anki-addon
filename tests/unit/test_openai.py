from addon.infrastructure.external_services.openai import OpenAIClient


def test_llm_engine_collab(addon_config):
    # Given
    expected = "ciao"
    openai_client = OpenAIClient.create_null(addon_config, [expected])
    prompt = "What is the Italian word for hello?"

    # When
    result = openai_client.run(prompt)

    # Then
    assert result == expected
