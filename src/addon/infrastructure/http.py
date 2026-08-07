"""Shared HTTP plumbing for LLM provider adapters."""

from __future__ import annotations

from typing import cast

import requests
import requests.exceptions

from .protocols import HttpClient, HttpResponse


class RequestsHttpClient:
    """Adapter that wraps the requests library to implement HttpClient."""

    def post(
        self,
        url: str,
        json: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        # requests.Response provides the full HttpResponse surface; the cast
        # is needed because ty infers status_code as None from requests'
        # untyped __init__.
        response = requests.post(url, json=json, headers=headers)
        return cast(HttpResponse, response)


def post_json(
    http: HttpClient,
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
) -> dict:
    """POST a JSON payload and return the parsed response body.

    Translates transport and HTTP errors into exceptions that name the
    failing endpoint, so adapter callers get actionable error messages.
    """
    try:
        response = http.post(url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            f"Cannot reach LLM server at {url}. "
            "Check if the inference server is running."
        ) from e

    if response.status_code != 200:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text
        raise RuntimeError(
            f"LLM server returned error {response.status_code} "
            f"for {url}. "
            f"Response: {error_body}"
        )
    return response.json()
