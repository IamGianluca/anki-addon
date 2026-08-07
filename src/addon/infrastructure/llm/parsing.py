"""Helpers for parsing text emitted by LLM providers."""

from __future__ import annotations

import re

_MARKDOWN_FENCE_RE = re.compile(r"^```(?:\w+)?\n?(.*?)\n?```$", re.DOTALL)


def strip_markdown_fence(text: str) -> str:
    """Remove a wrapping ``` code fence, if present.

    Models sometimes wrap structured output in a markdown fence even when
    asked for raw JSON; downstream JSON parsing expects the bare payload.
    """
    return _MARKDOWN_FENCE_RE.sub(r"\1", text.strip())
