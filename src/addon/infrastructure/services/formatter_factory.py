from __future__ import annotations

from ...application.services.formatter_service import NoteFormatter
from ...infrastructure.configuration.settings import (
    OpenAIConfig,
    load_raw_config,
)
from ...infrastructure.external_services.openai import OpenAIClient

# Module-level cache: populated on first call, reused for the session.
_cached_formatter: NoteFormatter | None = None


def get_formatter() -> NoteFormatter:
    """Return the singleton NoteFormatter, creating it lazily on first call."""
    global _cached_formatter
    if _cached_formatter is not None:
        return _cached_formatter

    from aqt import mw

    client = OpenAIClient(OpenAIConfig(load_raw_config(mw.addonManager)))
    _cached_formatter = NoteFormatter(client)
    return _cached_formatter
