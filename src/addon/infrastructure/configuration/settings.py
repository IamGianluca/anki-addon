from __future__ import annotations

import os
from typing import Optional

from ...utils import ensure_config


class AddonConfig:
    """Configuration adapter that bridges Anki's addon settings with application logic.

    This class abstracts the complexity of Anki's configuration system, providing
    a clean interface for accessing addon settings set by the user. These settings
    are currently limited to inference provider and LLM settings.

    The class supports two configuration sources: Anki's internal addon configuration
    for production use, and environment variables for testing/development scenarios.

    The class handles the transformation of raw configuration data into a
    structured format with validation and defaults, ensuring the addon
    has consistent access to required settings regardless of the source.

    Attributes:
        url: Complete HTTP URL for the OpenAI-compatible API endpoint.
        model_name: Name of the language model to use for completions.
        temperature: Sampling temperature for the language model (0.0-2.0).
        max_tokens: Maximum number of tokens to generate in completions.
        top_p: Nucleus sampling parameter (optional, LLM-specific).
        top_k: Top-k sampling parameter (optional, LLM-specific).
        min_p: Minimum probability threshold (optional, LLM-specific).
    """

    @staticmethod
    def create(addon_manager) -> AddonConfig:  # forward reference
        c: dict = ensure_config(addon_manager.getConfig("anki-addon"))
        config = dict()
        config["host"] = c.get("openai_host")
        config["port"] = c.get("openai_port")
        config["mode"] = c.get("openai_mode", "v1/chat/completions")
        config["model_name"] = c.get("openai_model")
        config["temperature"] = c.get("openai_temperature", 0.0)
        config["max_tokens"] = c.get("openai_max_tokens", 200)
        # These parameters are optional, and needed only for certain LLMs
        if c.get("openai_top_p"):
            config["top_p"] = float(c.get("openai_top_p"))
        if c.get("openai_top_k"):
            config["top_k"] = int(c.get("openai_top_k"))
        if c.get("openai_min_p"):
            config["min_p"] = float(c.get("openai_min_p"))
        return AddonConfig(config)

    @staticmethod
    def create_nullable(
        kwargs: Optional[dict] = None,
    ) -> AddonConfig:  # forward reference
        config = dict()
        config["host"] = os.environ.get("OPENAI_HOST")
        config["port"] = os.environ.get("OPENAI_PORT")
        config["mode"] = os.environ.get("OPENAI_MODE", "v1/chat/completions")
        config["model_name"] = os.environ.get("OPENAI_MODEL")
        config["temperature"] = float(
            os.environ.get("OPENAI_TEMPERATURE", "0.0")
        )
        config["max_tokens"] = int(os.environ.get("OPENAI_MAX_TOKENS", "500"))

        # Optional LLM parameters if set in .envrc or env variable
        if os.environ.get("OPENAI_TOP_P"):
            config["top_p"] = float(os.environ.get("OPENAI_TOP_P"))
        if os.environ.get("OPENAI_TOP_K"):
            config["top_k"] = int(os.environ.get("OPENAI_TOP_K"))
        if os.environ.get("OPENAI_MIN_P"):
            config["min_p"] = float(os.environ.get("OPENAI_MIN_P"))

        if kwargs:
            config.update(kwargs)

        return AddonConfig(config)

    def __init__(self, config) -> None:
        self.url = f"http://{config['host']}:{config['port']}/{config['mode']}"
        self.model_name = config["model_name"]
        self.temperature = float(config["temperature"])
        self.max_tokens = int(config.get("max_tokens", 500))

        # Optional LLM parameters
        self.top_p = config.get("top_p")
        self.top_k = config.get("top_k")
        self.min_p = config.get("min_p")
