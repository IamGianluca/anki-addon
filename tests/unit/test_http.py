"""Tests for the shared HTTP plumbing.

The timeout behavior is exercised against a real socket that accepts
the connection and never answers — the same failure mode a stalled
inference server produces — so the test proves the adapter fails
promptly instead of blocking forever.
"""

from __future__ import annotations

import socket

import pytest
import requests

from addon.infrastructure.http import RequestsHttpClient, post_json
from addon.infrastructure.protocols import HttpClient, HttpResponse


class FailingHttpClient(HttpClient):
    """A client whose transport always times out."""

    def post(
        self,
        url: str,
        json: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        raise requests.exceptions.ReadTimeout("server never answered")


def test_timeout_becomes_an_actionable_error() -> None:
    # Given a transport that times out
    client = FailingHttpClient()

    # When a request is made
    with pytest.raises(TimeoutError, match="did not respond in time"):
        post_json(client, "http://example.test/v1/chat/completions", {})


def test_requests_http_client_fails_promptly_on_a_silent_server() -> None:
    # Given a server that accepts connections but never replies
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    client = RequestsHttpClient(timeout=(0.2, 0.2))

    try:
        # When a request is made
        with pytest.raises(requests.exceptions.Timeout):
            client.post(f"http://127.0.0.1:{port}/v1/chat/completions", {})
    finally:
        # Then it raised within the timeout instead of hanging
        server.close()
