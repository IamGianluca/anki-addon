import pytest
from tests.fakes.openai_fakes import FakeOpenAIClient

from addon.infrastructure.configuration.settings import AddonConfig


def test_llm_engine_collab(addon_config: AddonConfig) -> None:
    # Given
    expected = "ciao"
    openai_client = FakeOpenAIClient.create(addon_config, [expected])
    prompt = "What is the Italian word for hello?"

    # When
    result = openai_client.run(prompt)

    # Then
    assert result == expected


def test_openai_fake_client_returns_multiple_responses_in_sequence(
    addon_config: AddonConfig,
) -> None:
    # Given
    openai = FakeOpenAIClient.create(addon_config, ["response1", "response2"])

    # When
    result1 = openai.run("prompt1")
    result2 = openai.run("prompt2")

    # Then
    assert result1 == "response1"
    assert result2 == "response2"


def test_openai_fake_client_exhausts_responses(
    addon_config: AddonConfig,
) -> None:
    # Given
    openai = FakeOpenAIClient.create(addon_config, ["response1"])

    # When
    result1 = openai.run("prompt")

    # Then
    assert result1 == "response1"

    # When/Then - responses exhausted, should return an Exception
    with pytest.raises(Exception):
        openai.run("prompt")
