from __future__ import annotations

from ...utils import ensure_config


class AddonConfig:
    """Configuration adapter that bridges Anki's addon settings with
    application logic.

    This class abstracts the complexity of Anki's configuration system,
    providing a clean interface for accessing addon settings set by the user.
    These settings are currently limited to inference provider and LLM settings.

    The class handles the transformation of raw configuration data from
    Anki's addon manager into a structured format with validation and
    defaults.

    Attributes:
        url: Complete HTTP URL for the OpenAI-compatible API endpoint.
        model_name: Name of the language model to use for completions.
        temperature: Sampling temperature for the language model (0.0-2.0).
        max_tokens: Maximum number of tokens to generate in completions.
        top_p: Nucleus sampling parameter (optional, LLM-specific).
        top_k: Top-k sampling parameter (optional, LLM-specific).
        min_p: Minimum probability threshold (optional, LLM-specific).
        reasoning: Whether to enable the model's reasoning (thinking) mode.
            Set to False to skip reasoning tokens, saving tokens and latency.
        preserve_thinking: Whether to preserve reasoning tokens in the output
            (optional, for models like Qwen3.6 with thinking mode).
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
        if top_p := c.get("openai_top_p"):
            config["top_p"] = float(top_p)
        if top_k := c.get("openai_top_k"):
            config["top_k"] = int(top_k)
        if min_p := c.get("openai_min_p"):
            config["min_p"] = float(min_p)
        config["reasoning"] = bool(c.get("openai_reasoning", False))
        config["preserve_thinking"] = bool(
            c.get("openai_preserve_thinking", False)
        )
        return AddonConfig(config)

    def __init__(self, config) -> None:
        missing = [
            key
            for key in ("host", "port", "model_name")
            if not config.get(key)
        ]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        self.url = f"http://{config['host']}:{config['port']}/{config['mode']}"
        self.model_name = config["model_name"]
        self.temperature = float(config["temperature"])
        self.max_tokens = int(config.get("max_tokens", 500))

        # Optional LLM parameters
        self.top_p = config.get("top_p")
        self.top_k = config.get("top_k")
        self.min_p = config.get("min_p")
        self.reasoning = bool(config.get("reasoning", False))
        self.preserve_thinking = bool(config.get("preserve_thinking", False))
