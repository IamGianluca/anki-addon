"""Tests for provider selection in create_completion_provider."""

from __future__ import annotations

import pytest
from tests.fakes.aqt_fakes import FakeAddonManager

from addon.infrastructure.external_services.openai import OpenAIClient
from addon.infrastructure.external_services.opencode_go import (
    OpenCodeGoClient,
)
from addon.infrastructure.services.completion_provider_factory import (
    create_completion_provider,
)

_OPENAI_CONFIG = {
    "openai_host": "localhost",
    "openai_port": "8000",
    "openai_model": "test-model",
}

_OPENCODE_GO_CONFIG = {
    "opencode_go_api_key": "test-key",
    "opencode_go_model": "glm-5.2",
}


def test_defaults_to_openai_client() -> None:
    # Given — no llm_provider key, as in pre-existing user configs
    addon_manager = FakeAddonManager(_OPENAI_CONFIG)

    # When
    provider = create_completion_provider(addon_manager)

    # Then
    assert isinstance(provider, OpenAIClient)


def test_returns_opencode_go_client_when_selected() -> None:
    # Given
    addon_manager = FakeAddonManager(
        {"llm_provider": "opencode_go", **_OPENCODE_GO_CONFIG}
    )

    # When
    provider = create_completion_provider(addon_manager)

    # Then
    assert isinstance(provider, OpenCodeGoClient)


def test_raises_on_unknown_provider() -> None:
    # Given
    addon_manager = FakeAddonManager({"llm_provider": "bogus"})

    # When / Then
    with pytest.raises(ValueError, match="Unknown llm_provider"):
        create_completion_provider(addon_manager)
