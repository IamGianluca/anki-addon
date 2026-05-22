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
