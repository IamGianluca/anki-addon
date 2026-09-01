from __future__ import annotations

from typing import Union

from ...infrastructure.configuration.settings import OpenAIConfig
from ...infrastructure.http import RequestsHttpClient, post_json
from ...infrastructure.llm.parsing import strip_markdown_fence
from ...infrastructure.protocols import HttpClient


class OpenAIClient:
    """HTTP client adapter for OpenAI-compatible inference servers.

    This class abstracts the communication with OpenAI-compatible API
    endpoints, such as vLLM servers, providing a unified interface for
    text generation.

    The client handles connection errors gracefully and transforms them into
    domain-specific exceptions with helpful error messages for debugging
    server connectivity issues.

    Implements CompletionProvider protocol.
    """

    def __init__(
        self,
        config: OpenAIConfig,
        http_client: HttpClient | None = None,
    ) -> None:
        self._config = config
        self._http_client: HttpClient = http_client or RequestsHttpClient()
        self._is_chat_completion = "chat/completions" in config.url
        self.last_reasoning_content: str | None = None

    def run(
        self,
        prompt: Union[str, list[dict]],
        **kwargs,
    ) -> str:
        """Generate text using the configured LLM endpoint.

        The input format depends on the endpoint configured in OpenAIConfig:
        - Chat Completions (/v1/chat/completions): Pass list of message dicts
        - Completions (/v1/completions): Pass string prompt

        Args:
            prompt: The input prompt (string or chat messages).
            **kwargs: Extra parameters forwarded to the inference server
                (e.g., guided_json for structured output).

        Returns the generated text from the content field.
        """
        optional_params = {}
        if self._config.top_p is not None:
            optional_params["top_p"] = self._config.top_p
        if self._config.top_k is not None:
            optional_params["top_k"] = self._config.top_k
        if self._config.min_p is not None:
            optional_params["min_p"] = self._config.min_p

        if self._is_chat_completion:
            payload = {
                "model": self._config.model_name,
                "messages": prompt,
                "max_tokens": self._config.max_tokens,
                "temperature": self._config.temperature,
                **optional_params,
            }
        else:
            payload = {
                "model": self._config.model_name,
                "prompt": prompt,
                "max_tokens": self._config.max_tokens,
                "temperature": self._config.temperature,
                **optional_params,
            }

        if not self._config.reasoning:
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        elif self._config.preserve_thinking:
            # See: https://unsloth.ai/docs/models/qwen3.6#thinking-enable-disable--preserve-thinking
            payload["chat_template_kwargs"] = {"preserve_thinking": True}

        if kwargs:
            # Incorporate extra parameters like `guided_json` schema
            payload.update(kwargs)

        headers = None
        if self._config.api_key:
            headers = {"Authorization": f"Bearer {self._config.api_key}"}
        response_data = post_json(
            self._http_client, self._config.url, payload, headers=headers
        )
        if self._is_chat_completion:
            message = response_data["choices"][0]["message"]
            text = message["content"]
            # llama.cpp reports thinking as reasoning_content; vLLM uses
            # the OpenAI-compatible "reasoning" field for Qwen3 models.
            self.last_reasoning_content = message.get("reasoning_content") or message.get("reasoning")
        else:
            text = response_data["choices"][0]["text"]
            self.last_reasoning_content = None
        return strip_markdown_fence(text)
