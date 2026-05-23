from __future__ import annotations

from ..protocols import ConfigProvider


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

    def __init__(self, config_provider: ConfigProvider) -> None:
        raw = config_provider.getConfig("anki-addon")
        if raw is None:
            raise RuntimeError("Addon config not initialized")

        host = raw.get("openai_host")
        port = raw.get("openai_port")
        model_name = raw.get("openai_model")

        missing = [
            key
            for key, value in zip(
                ("host", "port", "model_name"), (host, port, model_name)
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        mode = raw.get("openai_mode", "v1/chat/completions")
        self.url = f"http://{host}:{port}/{mode}"
        self.model_name = model_name
        self.temperature = float(raw.get("openai_temperature", 0.0))
        self.max_tokens = int(raw.get("openai_max_tokens", 200))

        # Optional LLM parameters
        self.top_p = (
            float(raw["openai_top_p"]) if raw.get("openai_top_p") else None
        )
        self.top_k = (
            int(raw["openai_top_k"]) if raw.get("openai_top_k") else None
        )
        self.min_p = (
            float(raw["openai_min_p"]) if raw.get("openai_min_p") else None
        )
        self.reasoning = bool(raw.get("openai_reasoning", False))
        self.preserve_thinking = bool(
            raw.get("openai_preserve_thinking", False)
        )
