"""Fixtures for the LLM eval suite.

The client is configured from the same env vars as the integration
tests (.envrc): OPENAI_HOST, OPENAI_PORT, OPENAI_MODEL, plus the
optional OPENAI_* sampling and reasoning overrides — so an eval run
measures the same model and settings the addon uses in production.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from addon.infrastructure.configuration.settings import OpenAIConfig
from addon.infrastructure.external_services.openai import OpenAIClient

RESULTS_DIR = Path(__file__).parent / "results"

_REQUIRED_ENV = ("OPENAI_HOST", "OPENAI_PORT", "OPENAI_MODEL")
_OPTIONAL_ENV = {
    "OPENAI_MODE": "openai_mode",
    "OPENAI_TEMPERATURE": "openai_temperature",
    "OPENAI_MAX_TOKENS": "openai_max_tokens",
    "OPENAI_TOP_P": "openai_top_p",
    "OPENAI_TOP_K": "openai_top_k",
    "OPENAI_MIN_P": "openai_min_p",
    "OPENAI_REASONING": "openai_reasoning",
    "OPENAI_PRESERVE_THINKING": "openai_preserve_thinking",
}
_BOOL_ENV = {"OPENAI_REASONING", "OPENAI_PRESERVE_THINKING"}


@pytest.fixture(scope="session")
def eval_config() -> OpenAIConfig:
    missing = [key for key in _REQUIRED_ENV if not os.environ.get(key)]
    if missing:
        pytest.skip(f"eval env vars not set: {', '.join(missing)}")
    raw = {key.lower(): os.environ[key] for key in _REQUIRED_ENV}
    for env_key, config_key in _OPTIONAL_ENV.items():
        value = os.environ.get(env_key)
        if not value:
            continue
        raw[config_key] = (
            value.lower() == "true" if env_key in _BOOL_ENV else value
        )
    # The addon default (200) truncates agent steps; evals need room
    # for a full JSON action per turn.
    raw.setdefault("openai_max_tokens", "8192")
    return OpenAIConfig(raw)


@pytest.fixture(scope="session")
def llm_client(eval_config: OpenAIConfig) -> OpenAIClient:
    return OpenAIClient(eval_config)


@pytest.fixture(scope="session")
def eval_results_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path
