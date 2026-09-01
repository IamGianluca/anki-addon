"""Fixtures for the LLM eval suite.

The provider is selected via the LLM_PROVIDER env var (default "openai")
and configured from the same env vars as the integration tests (.envrc):

- openai (self-hosted): OPENAI_HOST, OPENAI_PORT, OPENAI_MODEL, plus the
  optional OPENAI_* sampling/reasoning overrides. An API key is read from
  OPENAI_API_KEY and sent as a Bearer token for servers that require auth.
- opencode_go: OPENCODE_GO_API_KEY, OPENCODE_GO_MODEL, plus the optional
  OPENCODE_GO_TEMPERATURE / OPENCODE_GO_MAX_TOKENS overrides.

The client is built through create_completion_provider — the same
factory the addon uses in production — so an eval run measures the same
provider wiring the addon ships with.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from tests.fakes.aqt_fakes import FakeAddonManager

from addon.application.protocols import CompletionProvider
from addon.infrastructure.services.completion_provider_factory import (
    create_completion_provider,
)

RESULTS_DIR = Path(__file__).parent / "results"

_OPENAI_REQUIRED_ENV = ("OPENAI_HOST", "OPENAI_PORT", "OPENAI_MODEL")
_OPENAI_OPTIONAL_ENV = {
    "OPENAI_MODE": "openai_mode",
    "OPENAI_TEMPERATURE": "openai_temperature",
    "OPENAI_MAX_TOKENS": "openai_max_tokens",
    "OPENAI_TOP_P": "openai_top_p",
    "OPENAI_TOP_K": "openai_top_k",
    "OPENAI_MIN_P": "openai_min_p",
    "OPENAI_REASONING": "openai_reasoning",
    "OPENAI_PRESERVE_THINKING": "openai_preserve_thinking",
    "OPENAI_API_KEY": "openai_api_key",
}
_BOOL_ENV = {"OPENAI_REASONING", "OPENAI_PRESERVE_THINKING"}

_OPENCODE_GO_REQUIRED_ENV = ("OPENCODE_GO_API_KEY", "OPENCODE_GO_MODEL")
_OPENCODE_GO_OPTIONAL_ENV = {
    "OPENCODE_GO_TEMPERATURE": "opencode_go_temperature",
    "OPENCODE_GO_MAX_TOKENS": "opencode_go_max_tokens",
}


def _read_env_config(
    required: tuple[str, ...], optional: dict[str, str]
) -> dict:
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        pytest.skip(f"eval env vars not set: {', '.join(missing)}")
    raw = {key.lower(): os.environ[key] for key in required}
    for env_key, config_key in optional.items():
        value = os.environ.get(env_key)
        if not value:
            continue
        raw[config_key] = (
            value.lower() == "true" if env_key in _BOOL_ENV else value
        )
    return raw


@pytest.fixture(scope="session")
def eval_config() -> dict:
    global _eval_model
    provider = os.environ.get("LLM_PROVIDER", "openai")
    if provider == "opencode_go":
        raw = _read_env_config(
            _OPENCODE_GO_REQUIRED_ENV, _OPENCODE_GO_OPTIONAL_ENV
        )
    else:
        raw = _read_env_config(_OPENAI_REQUIRED_ENV, _OPENAI_OPTIONAL_ENV)
    # The addon defaults truncate agent steps (200) or starve reasoning
    # models; evals need room for a full JSON action per turn.
    raw.setdefault(f"{provider}_max_tokens", "8192")
    raw["llm_provider"] = provider
    _eval_model = raw.get(f"{provider}_model")
    return raw


@pytest.fixture(scope="session")
def llm_client(eval_config: dict) -> CompletionProvider:
    return create_completion_provider(FakeAddonManager(eval_config))


@pytest.fixture(scope="session")
def eval_results_dir() -> Path:
    global _eval_results_dir
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / stamp
    path.mkdir(parents=True, exist_ok=True)
    _eval_results_dir = path
    return path


# Module-level state for the session hooks (can't access fixtures from hooks).
_eval_start: float = 0
_eval_results_dir: Path | None = None
_eval_model: str | None = None


def pytest_sessionstart(session: pytest.Session) -> None:
    global _eval_start
    _eval_start = time.monotonic()


def pytest_sessionfinish(session: pytest.Session) -> None:
    elapsed = time.monotonic() - _eval_start
    target = _eval_results_dir
    if target is None:
        # Fallback: most recent results directory.
        runs = sorted(p for p in RESULTS_DIR.iterdir() if p.is_dir())
        if runs:
            target = runs[-1]
    if target is not None:
        meta = {
            "elapsed_seconds": round(elapsed, 1),
            "model": _eval_model or "unknown",
            "tasks_collected": session.testscollected,
        }
        (target / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
