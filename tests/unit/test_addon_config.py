from __future__ import annotations

from tests.fakes.aqt_fakes import FakeAddonManager

from addon.infrastructure.configuration.settings import AddonConfig


def test_defaults_notetype_names_when_not_in_config() -> None:
    # Given
    addon_manager = FakeAddonManager({})

    # When
    config = AddonConfig(addon_manager)

    # Then
    assert config.basic_notetype == "Basic"
    assert config.cloze_notetype == "Cloze"


def test_reads_custom_notetype_names_from_config() -> None:
    # Given
    addon_manager = FakeAddonManager(
        {
            "basic_notetype_name": "Better Markdown : Basic",
            "cloze_notetype_name": "Better Markdown : Cloze",
        }
    )

    # When
    config = AddonConfig(addon_manager)

    # Then
    assert config.basic_notetype == "Better Markdown : Basic"
    assert config.cloze_notetype == "Better Markdown : Cloze"
