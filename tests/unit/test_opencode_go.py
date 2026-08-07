"""Adapter tests for OpenCodeGoClient.

These tests exercise OpenCodeGoClient's real logic (auth, payload building,
response parsing, error handling) using FakeHttpClient to avoid real
network calls.
"""

from __future__ import annotations

import pytest
import requests.exceptions
from tests.fakes.openai_fakes import FakeHttpClient

from addon.infrastructure.configuration.settings import OpenCodeGoConfig
from addon.infrastructure.external_services.opencode_go import (
    OpenCodeGoClient,
)
from addon.infrastructure.protocols import HttpClient

GATEWAY_URL = "https://opencode.ai/zen/go/v1/chat/completions"


def _create_config(overrides: dict | None = None) -> OpenCodeGoConfig:
    base = {
        "opencode_go_api_key": "test-key",
        "opencode_go_model": "glm-5.2",
    }
    base.update(overrides or {})
    return OpenCodeGoConfig(base)


def _create_client(
    http: HttpClient, config_overrides: dict | None = None
) -> OpenCodeGoClient:
    return OpenCodeGoClient(_create_config(config_overrides), http_client=http)


# --- Config ---


def test_config_requires_api_key_and_model() -> None:
    # Given / When / Then
    with pytest.raises(ValueError) as exc_info:
        OpenCodeGoConfig({})

    assert "opencode_go_api_key" in str(exc_info.value)
    assert "opencode_go_model" in str(exc_info.value)


def test_config_defaults() -> None:
    # Given / When
    config = _create_config()

    # Then
    assert config.temperature == 0.0
    # Higher than the self-hosted default: curator steps need room
    assert config.max_tokens == 8192


# --- Payload construction and auth ---


def test_builds_chat_payload() -> None:
    # Given
    http = FakeHttpClient()
    client = _create_client(http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_url == GATEWAY_URL
    assert http.last_payload is not None
    assert http.last_payload["model"] == "glm-5.2"
    assert http.last_payload["messages"] == [{"role": "user", "content": "hi"}]
    assert http.last_payload["temperature"] == 0.0
    assert http.last_payload["max_tokens"] == 8192


def test_sends_api_key_as_bearer_token() -> None:
    # Given
    http = FakeHttpClient()
    client = _create_client(http)

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert http.last_headers == {"Authorization": "Bearer test-key"}


def test_forwards_extra_kwargs() -> None:
    # Given
    http = FakeHttpClient()
    client = _create_client(http)

    # When
    client.run(
        [{"role": "user", "content": "hi"}],
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": {"type": "object"}},
        },
    )

    # Then
    assert http.last_payload is not None
    assert "response_format" in http.last_payload


def test_rejects_string_prompt() -> None:
    # Given
    client = _create_client(FakeHttpClient())

    # When / Then
    with pytest.raises(ValueError, match="list of messages"):
        client.run("raw prompt")


@pytest.mark.parametrize(
    "model", ["gpt-5.6-luna", "minimax-m3", "qwen3.7-plus", "qwen3.6-plus"]
)
def test_rejects_models_served_via_other_api_flavors(model: str) -> None:
    # Given / When / Then
    with pytest.raises(ValueError, match="chat/completions"):
        _create_client(FakeHttpClient(), {"opencode_go_model": model})


# --- Response parsing ---


def test_returns_content_from_chat_response() -> None:
    # Given
    body = {"choices": [{"message": {"content": "hello world"}}]}
    client = _create_client(FakeHttpClient(json_body=body))

    # When
    result = client.run([{"role": "user", "content": "hi"}])

    # Then
    assert result == "hello world"


def test_strips_markdown_fences() -> None:
    # Given
    body = {
        "choices": [{"message": {"content": '```json\n{"key": "val"}\n```'}}]
    }
    client = _create_client(FakeHttpClient(json_body=body))

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
    client = _create_client(FakeHttpClient(json_body=body))

    # When
    client.run([{"role": "user", "content": "hi"}])

    # Then
    assert client.last_reasoning_content == "let me think..."


def test_falls_back_to_reasoning_content_when_content_is_empty() -> None:
    # Given — observed gateway behavior with glm-5.2: the whole reply
    # lands in reasoning_content, content is "", finish_reason is "stop"
    body = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "reasoning_content": '{"ok": true}',
                },
                "finish_reason": "stop",
            }
        ]
    }
    client = _create_client(FakeHttpClient(json_body=body))

    # When
    result = client.run([{"role": "user", "content": "hi"}])

    # Then
    assert result == '{"ok": true}'


def test_raises_when_content_empty_due_to_length() -> None:
    # Given — thinking truncated mid-turn: the partial reasoning is not
    # a usable response, so the fallback must not apply
    body = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "reasoning_content": "1. **Analyze the request:**...",
                },
                "finish_reason": "length",
            }
        ]
    }
    client = _create_client(FakeHttpClient(json_body=body))

    # When / Then
    with pytest.raises(RuntimeError, match="opencode_go_max_tokens"):
        client.run([{"role": "user", "content": "hi"}])


def test_raises_on_empty_content() -> None:
    # Given — e.g. max_tokens hit before any content was produced
    body = {
        "choices": [{"message": {"content": None}, "finish_reason": "length"}]
    }
    client = _create_client(FakeHttpClient(json_body=body))

    # When / Then
    with pytest.raises(RuntimeError, match="empty content"):
        client.run([{"role": "user", "content": "hi"}])


# --- Error handling ---


def test_raises_on_connection_error() -> None:
    # Given
    class FailingHttpClient(HttpClient):
        def post(self, url, json=None, headers=None):
            raise requests.exceptions.ConnectionError("refused")

    client = _create_client(FailingHttpClient())

    # When / Then
    with pytest.raises(ConnectionError, match="Cannot reach LLM server"):
        client.run([{"role": "user", "content": "hi"}])


def test_raises_on_non_200_response() -> None:
    # Given
    body = {"error": {"message": "invalid api key"}}
    http = FakeHttpClient(status_code=401, json_body=body)
    client = _create_client(http)

    # When / Then
    with pytest.raises(RuntimeError, match="LLM server returned error 401"):
        client.run([{"role": "user", "content": "hi"}])
