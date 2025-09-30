import pytest

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


def test_openai_null_client_returns_multiple_responses_in_sequence(
    addon_config,
):
    # Given
    openai = OpenAIClient.create_null(addon_config, ["response1", "response2"])

    # When
    result1 = openai.run("prompt1")
    result2 = openai.run("prompt2")

    # Then
    assert result1 == "response1"
    assert result2 == "response2"


def test_openai_null_client_exhausts_responses(addon_config):
    # Given
    openai = OpenAIClient.create_null(addon_config, ["response1"])

    # When
    result1 = openai.run("prompt")

    # Then
    assert result1 == "response1"

    # When/Then - responses exhausted, should return an Exception
    with pytest.raises(Exception):
        openai.run("prompt")
