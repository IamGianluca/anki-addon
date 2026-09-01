from __future__ import annotations

import pytest

from addon.infrastructure.configuration.settings import OpenAIConfig


def _create_config(overrides: dict | None = None) -> OpenAIConfig:
    base = {
        "openai_host": "localhost",
        "openai_port": "8000",
        "openai_model": "test-model",
    }
    base.update(overrides or {})
    return OpenAIConfig(base)


def test_reads_required_parameters() -> None:
    # Given / When
    config = _create_config({"openai_temperature": 0.7})

    # Then
    assert config.url == "http://localhost:8000/v1/chat/completions"
    assert config.model_name == "test-model"
    assert config.temperature == 0.7


def test_defaults_temperature_when_not_in_config() -> None:
    # Given / When
    config = _create_config()

    # Then
    assert config.temperature == 0.0


def test_reads_max_tokens() -> None:
    # Given / When
    config = _create_config({"openai_max_tokens": 300})

    # Then
    assert config.max_tokens == 300


def test_defaults_max_tokens_when_not_in_config() -> None:
    # Given / When
    config = _create_config()

    # Then
    assert config.max_tokens == 200


def test_reads_optional_sampling_parameters() -> None:
    # Given / When
    config = _create_config(
        {
            "openai_top_p": "0.9",
            "openai_top_k": "40",
            "openai_min_p": "0.1",
        }
    )

    # Then
    assert config.top_p == 0.9
    assert config.top_k == 40
    assert config.min_p == 0.1


def test_optional_parameters_are_none_when_not_in_config() -> None:
    # Given / When
    config = _create_config()

    # Then
    assert config.top_p is None
    assert config.top_k is None
    assert config.min_p is None


def test_reads_api_key() -> None:
    # Given / When
    config = _create_config({"openai_api_key": "sk-test"})

    # Then
    assert config.api_key == "sk-test"


def test_api_key_defaults_to_none() -> None:
    # Given / When
    config = _create_config()

    # Then
    assert config.api_key is None


def test_blank_api_key_is_none() -> None:
    # Given / When
    config = _create_config({"openai_api_key": ""})

    # Then
    assert config.api_key is None


@pytest.mark.parametrize(
    "config,expected_missing",
    [
        ({"openai_port": "8000", "openai_model": "test-model"}, ["host"]),
        ({"openai_host": "localhost", "openai_model": "test-model"}, ["port"]),
        ({"openai_host": "localhost", "openai_port": "8000"}, ["model_name"]),
        ({}, ["host", "port", "model_name"]),
    ],
)
def test_raises_value_error_when_required_params_missing(
    config: dict, expected_missing: list[str]
) -> None:
    # Given / When / Then
    with pytest.raises(ValueError) as exc_info:
        OpenAIConfig(config)

    error_msg = str(exc_info.value)
    for key in expected_missing:
        assert key in error_msg
