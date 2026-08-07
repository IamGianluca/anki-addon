"""Composition helper: build the CompletionProvider chosen in the config."""

from __future__ import annotations

from ...application.protocols import CompletionProvider
from ...infrastructure.configuration.settings import (
    OpenAIConfig,
    OpenCodeGoConfig,
    load_raw_config,
)
from ...infrastructure.external_services.openai import OpenAIClient
from ...infrastructure.external_services.opencode_go import OpenCodeGoClient
from ...infrastructure.protocols import ConfigProvider


def create_completion_provider(
    config_provider: ConfigProvider,
) -> CompletionProvider:
    """Build the completion provider selected by the llm_provider setting.

    Both composition roots (note formatter, curator agent) go through here
    so provider selection lives in exactly one place.
    """
    raw = load_raw_config(config_provider)
    provider = raw.get("llm_provider", "openai")
    if provider == "opencode_go":
        return OpenCodeGoClient(OpenCodeGoConfig(raw))
    if provider == "openai":
        return OpenAIClient(OpenAIConfig(raw))
    raise ValueError(
        f"Unknown llm_provider: {provider!r}. "
        "Expected 'openai' or 'opencode_go'."
    )
