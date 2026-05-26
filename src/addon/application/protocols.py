"""Protocols defining ports that the application layer depends on."""

from __future__ import annotations

from typing import Protocol


class CompletionProvider(Protocol):
    """Port for generating text completions.

    Captures what the application needs from any provider: send a prompt,
    get text back. Concrete adapters (OpenAI, Anthropic, Google, etc.)
    implement this port. The application does not know or care which
    provider is behind the interface.
    """

    def run(self, prompt: str | list[dict], **kwargs) -> str: ...
