from __future__ import annotations

import os

from aqt.main import AnkiQt

from ...utils import ensure_config


class AddonConfig:
    """Configuration adapter that bridges Anki's addon settings with application logic.

    This class abstracts the complexity of Anki's configuration system, providing
    a clean interface for accessing OpenAI server settings. It supports two
    configuration sources: Anki's internal addon configuration for production
    use, and environment variables for testing/development scenarios.

    The class handles the transformation of raw configuration data into a
    structured format with validation and defaults, ensuring the application
    has consistent access to required settings regardless of the source.

    Attributes:
        url: Complete HTTP URL for the OpenAI-compatible API endpoint.
        model_name: Name of the language model to use for completions.
    """

    @staticmethod
    def create(mw: AnkiQt) -> AddonConfig:  # forward reference
        c: dict = ensure_config(mw.addonManager.getConfig("anki-addon"))
        config = dict()
        config["host"] = c.get("openai_host")
        config["port"] = c.get("openai_port")
        config["model_name"] = c.get("openai_model")
        return AddonConfig(config)

    @staticmethod
    def create_nullable() -> AddonConfig:  # forward reference
        config = dict()
        config["host"] = os.environ.get("OPENAI_HOST")
        config["port"] = os.environ.get("OPENAI_PORT")
        config["model_name"] = os.environ.get("OPENAI_MODEL")
        return AddonConfig(config)

    def __init__(self, config) -> None:
        self.url = f"http://{config['host']}:{config['port']}/v1/completions"
        self.model_name = config["model_name"]
