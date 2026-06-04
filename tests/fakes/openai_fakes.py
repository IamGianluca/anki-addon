"""Test doubles for LLM interactions.

Two fakes at different levels:

- FakeCompletionProvider: fakes the entire completion port. Used in
  service-layer tests to return canned responses without any HTTP wiring.
- FakeHttpClient: fakes only the HTTP layer. Used in adapter tests to
  exercise OpenAIClient's real logic (payload building, response parsing,
  etc.) while avoiding real network calls.
"""

from __future__ import annotations

from addon.application.protocols import CompletionProvider
from addon.infrastructure.protocols import HttpClient, HttpResponse


class FakeCompletionProvider(CompletionProvider):
    """Fake completion provider for service-layer tests.

    Returns pre-configured responses and records prompts for verification.
    """

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or [])
        self.prompts_received: list[list[dict] | str] = []
        self.kwargs_received: list[dict] = []

    def run(self, prompt: str | list[dict], **kwargs) -> str:
        self.prompts_received.append(prompt)
        self.kwargs_received.append(kwargs)
        if not self.responses:
            raise RuntimeError(
                "No more responses configured on FakeCompletionProvider"
            )
        return self.responses.pop(0)


class FakeHttpClient(HttpClient):
    """Fake HTTP client for adapter-level tests.

    Implements the HttpClient port, recording calls for verification.
    """

    def __init__(
        self,
        status_code: int = 200,
        json_body: dict | None = None,
    ) -> None:
        self.last_url: str | None = None
        self.last_payload: dict | None = None
        self._status_code = status_code
        self._json_body = json_body or {
            "choices": [{"message": {"content": "ok"}}],
        }

    def post(self, url: str, json: dict | None = None) -> FakeResponse:
        self.last_url = url
        self.last_payload = json
        return FakeResponse(self._status_code, self._json_body)


class FakeResponse(HttpResponse):
    """Minimal requests.Response stand-in for adapter tests."""

    def __init__(self, status_code: int, body: dict) -> None:
        self._status_code = status_code
        self._body = body

    @property
    def status_code(self) -> int:
        return self._status_code

    def json(self) -> dict:
        return self._body

    @property
    def text(self) -> str:
        import json

        return json.dumps(self._body)
