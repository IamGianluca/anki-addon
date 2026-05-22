"""Protocols describing external APIs our addon depends on.

Defines the minimal contract our code needs from dependencies we don't control
(Anki, Qdrant, etc.). Production code depends on these, not on concrete
implementations. mypy verifies both real and fake implementations satisfy them.
"""

from __future__ import annotations

from typing import Any, Protocol


class ConfigProvider(Protocol):
    """Minimal contract for reading addon configuration from Anki's addon manager."""

    def getConfig(self, module: str) -> dict[str, Any] | None: ...


class HttpResponse(Protocol):
    """Minimal response contract that HTTP clients must produce."""

    @property
    def status_code(self) -> int: ...

    def json(self) -> dict: ...

    @property
    def text(self) -> str: ...


class HttpClient(Protocol):
    """Minimal HTTP client contract for making POST requests.

    Both real adapters (requests, httpx) and test fakes implement this port.
    """

    def post(self, url: str, json: dict | None = None) -> HttpResponse: ...
