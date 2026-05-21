"""Protocols defining ports that the application layer depends on."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Port for language model interaction.

    Captures what the application needs from an LLM provider: send a prompt,
    get text back. Concrete adapters (OpenAI, local models, etc.) implement
    this port.
    """

    def run(self, prompt: str | list[dict], **kwargs) -> str: ...
