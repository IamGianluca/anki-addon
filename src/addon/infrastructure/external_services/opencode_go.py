from __future__ import annotations

from typing import Union

from ...infrastructure.configuration.settings import OpenCodeGoConfig
from ...infrastructure.http import RequestsHttpClient, post_json
from ...infrastructure.llm.parsing import strip_markdown_fence
from ...infrastructure.protocols import HttpClient

_CHAT_COMPLETIONS_URL = "https://opencode.ai/zen/go/v1/chat/completions"

# OpenCode Go serves each model through exactly one API flavor. Only the
# chat/completions flavor is supported by this adapter; models served via
# the other flavors are rejected at construction with an actionable error.
_UNSUPPORTED_MODEL_APIS = {
    "gpt-5.6-luna": "OpenAI Responses API",
    "minimax-m3": "Anthropic Messages API",
    "minimax-m2.7": "Anthropic Messages API",
    "minimax-m2.5": "Anthropic Messages API",
    "qwen3.8-max": "Anthropic Messages API",
    "qwen3.7-max": "Anthropic Messages API",
    "qwen3.7-plus": "Anthropic Messages API",
    "qwen3.6-plus": "Anthropic Messages API",
}


class OpenCodeGoClient:
    """HTTP client adapter for the OpenCode Go subscription gateway.

    Wraps the gateway's OpenAI-compatible chat/completions endpoint,
    authenticating with the API key as a Bearer token. Unlike the
    self-hosted OpenAIClient, no chat-template or reasoning-toggle
    parameters are sent — those are vLLM/Qwen-specific and hosted
    providers reject unknown fields.

    Implements CompletionProvider protocol.

    Response quirk: the gateway's reasoning models sometimes put the
    entire reply in reasoning_content and leave content empty with
    finish_reason="stop" (observed with glm-5.2); the reasoning content
    is then returned as the response text. Empty content with any other
    finish_reason (e.g. "length") raises instead, since truncated
    thinking is never a usable response.
    """

    def __init__(
        self,
        config: OpenCodeGoConfig,
        http_client: HttpClient | None = None,
    ) -> None:
        unsupported_api = _UNSUPPORTED_MODEL_APIS.get(config.model)
        if unsupported_api:
            raise ValueError(
                f"Model {config.model!r} is served via the "
                f"{unsupported_api}, which this adapter does not support. "
                "Choose a model served via /chat/completions "
                "(GLM, Kimi, DeepSeek, MiMo, Grok, Hy3)."
            )
        self._config = config
        self._http_client: HttpClient = http_client or RequestsHttpClient()
        self.last_reasoning_content: str | None = None

    def run(
        self,
        prompt: Union[str, list[dict]],
        **kwargs,
    ) -> str:
        """Generate a chat completion via the OpenCode Go gateway.

        Args:
            prompt: Chat messages (list of role/content dicts). Raw string
                prompts are rejected — the gateway only serves chat models.
            **kwargs: Extra parameters forwarded to the gateway
                (e.g., response_format for structured output).

        Returns the generated text from the content field.
        """
        if isinstance(prompt, str):
            raise ValueError(
                "OpenCode Go only serves chat models; pass a list of messages."
            )
        payload = {
            "model": self._config.model,
            "messages": prompt,
            "max_tokens": self._config.max_tokens,
            "temperature": self._config.temperature,
            **kwargs,
        }
        headers = {"Authorization": f"Bearer {self._config.api_key}"}
        response_data = post_json(
            self._http_client, _CHAT_COMPLETIONS_URL, payload, headers=headers
        )
        choice = response_data["choices"][0]
        message = choice["message"]
        content = message.get("content")
        reasoning = message.get("reasoning_content")
        finish_reason = choice.get("finish_reason")
        if content and content.strip():
            text = content
            self.last_reasoning_content = reasoning
        elif reasoning and finish_reason == "stop":
            text = reasoning
            # The reasoning was the response, not separate thinking.
            self.last_reasoning_content = None
        else:
            raise RuntimeError(
                "OpenCode Go returned empty content "
                f"(finish_reason={finish_reason}). "
                "If finish_reason is 'length', raise opencode_go_max_tokens."
            )
        return strip_markdown_fence(text)
