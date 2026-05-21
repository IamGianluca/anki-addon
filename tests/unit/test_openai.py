"""Adapter tests for OpenAIClient.

These tests exercise OpenAIClient's real logic (payload building, response
parsing, error handling) using FakeHttpClient to avoid real network calls.
"""

from __future__ import annotations

import pytest
import requests.exceptions
from tests.fakes.aqt_fakes import FakeAddonManager
from tests.fakes.openai_fakes import FakeHttpClient

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient


def _create_config(overrides: dict | None = None) -> AddonConfig:
    """Build an AddonConfig for adapter tests."""
    base = {
        "openai_host": "localhost",
        "openai_port": "8000",
        "openai_model": "test-model",
    }
    base.update(overrides or {})
    return AddonConfig.create(FakeAddonManager(base))


# --- Payload construction ---


def test_builds_chat_payload() -> None:
    # Given
    http = FakeHttpClient()
    config = _create_config()
    client = OpenAIClient(config, http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_payload is not None
    assert http.last_payload["model"] == "test-model"
    assert http.last_payload["messages"] == [{"role": "user", "content": "hi"}]


def test_builds_completions_payload() -> None:
    # Given
    body = {"choices": [{"text": "hello world"}]}
    http = FakeHttpClient(json_body=body)
    config = _create_config({"openai_mode": "v1/completions"})
    client = OpenAIClient(config, http)

    # When
    client.run("hello world")

    # Then
    assert http.last_payload is not None
    assert http.last_payload["prompt"] == "hello world"


def test_disables_thinking_when_reasoning_off() -> None:
    # Given
    http = FakeHttpClient()
    # reasoning defaults to False when key is absent
    config = _create_config()
    client = OpenAIClient(config, http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_payload is not None
    assert http.last_payload["chat_template_kwargs"] == {
        "enable_thinking": False
    }


def test_preserves_thinking_when_configured() -> None:
    # Given
    http = FakeHttpClient()
    config = _create_config(
        {"openai_reasoning": "true", "openai_preserve_thinking": "true"}
    )
    client = OpenAIClient(config, http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_payload is not None
    assert http.last_payload["chat_template_kwargs"] == {
        "preserve_thinking": True
    }


def test_includes_optional_sampling_params() -> None:
    # Given
    http = FakeHttpClient()
    config = _create_config(
        {
            "openai_top_p": "0.9",
            "openai_top_k": "50",
            "openai_min_p": "0.05",
        }
    )
    client = OpenAIClient(config, http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_payload is not None
    assert http.last_payload["top_p"] == 0.9
    assert http.last_payload["top_k"] == 50
    assert http.last_payload["min_p"] == 0.05


def test_forwards_extra_kwargs() -> None:
    # Given
    http = FakeHttpClient()
    config = _create_config()
    client = OpenAIClient(config, http)
    schema = {"type": "object", "properties": {}}

    # When
    client.run(
        [{"role": "user", "content": "hi"}],
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": schema},
        },
    )

    # Then
    assert http.last_payload is not None
    assert "response_format" in http.last_payload


# --- Response parsing ---


def test_returns_content_from_chat_response() -> None:
    # Given
    body = {"choices": [{"message": {"content": "hello world"}}]}
    http = FakeHttpClient(json_body=body)
    config = _create_config()
    client = OpenAIClient(config, http)

    # When
    result = client.run([{"role": "user", "content": "hi"}])

    # Then
    assert result == "hello world"


def test_strips_markdown_fences() -> None:
    # Given
    body = {
        "choices": [{"message": {"content": '```json\n{"key": "val"}\n```'}}]
    }
    http = FakeHttpClient(json_body=body)
    config = _create_config()
    client = OpenAIClient(config, http)

    # When
    result = client.run([{"role": "user", "content": "hi"}])

    # Then
    assert result == '{"key": "val"}'


def test_captures_reasoning_content() -> None:
    # Given
    body = {
        "choices": [
            {
                "message": {
                    "content": "answer",
                    "reasoning_content": "let me think...",
                }
            }
        ]
    }
    http = FakeHttpClient(json_body=body)
    config = _create_config()
    client = OpenAIClient(config, http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert client.last_reasoning_content == "let me think..."


# --- Error handling ---


def test_raises_on_connection_error() -> None:
    # Given
    class FailingHttpClient:
        def post(self, url, json=None):
            raise requests.exceptions.ConnectionError("refused")

    config = _create_config()
    client = OpenAIClient(config, FailingHttpClient())

    # When / Then
    with pytest.raises(ConnectionError, match="Cannot reach LLM server"):
        client.run("prompt")


def test_raises_on_non_200_response() -> None:
    # Given
    body = {"error": {"message": "model not found"}}
    http = FakeHttpClient(status_code=404, json_body=body)
    config = _create_config()
    client = OpenAIClient(config, http)

    # When / Then
    with pytest.raises(RuntimeError, match="LLM server returned error 404"):
        client.run("prompt")
