from __future__ import annotations

import re
from typing import Union

import requests
import requests.exceptions

from ...infrastructure.configuration.settings import AddonConfig
from ...infrastructure.protocols import HttpClient

_REMOVE_MARKDOWN_FENCE_RE = re.compile(
    r"^```(?:\w+)?\n?(.*?)\n?```$", re.DOTALL
)


class RequestsHttpClient:
    """Adapter that wraps the requests library to implement HttpClient."""

    def post(self, url: str, json: dict | None = None) -> requests.Response:
        return requests.post(url, json=json)


class OpenAIClient:
    """HTTP client adapter for OpenAI-compatible inference servers.

    This class abstracts the communication with OpenAI-compatible API endpoints,
    such as vLLM servers, providing a unified interface for text generation.

    The client handles connection errors gracefully and transforms them into
    domain-specific exceptions with helpful error messages for debugging
    server connectivity issues.

    Implements LLMClient protocol.
    """

    def __init__(
        self,
        config: AddonConfig,
        http_client: HttpClient | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client or RequestsHttpClient()
        self._is_chat_completion = "chat/completions" in config.url
        self.last_reasoning_content: str | None = None

    def run(
        self,
        prompt: Union[str, list[dict]],
        **kwargs,
    ) -> str:
        """Generate text using the configured LLM endpoint.

        The input format depends on the API endpoint configured in AddonConfig:
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

        try:
            response = self._http_client.post(self._config.url, json=payload)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot reach LLM server at {self._config.url}. "
                "Check if the inference server is running."
            ) from e

        # Check for HTTP errors
        if response.status_code != 200:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            raise RuntimeError(
                f"LLM server returned error {response.status_code} for {self._config.url}. "
                f"Response: {error_body}"
            )

        response_data = response.json()
        if self._is_chat_completion:
            message = response_data["choices"][0]["message"]
            text = message["content"]
            self.last_reasoning_content = message.get("reasoning_content")
        else:
            text = response_data["choices"][0]["text"]
            self.last_reasoning_content = None
        return _REMOVE_MARKDOWN_FENCE_RE.sub(r"\1", text.strip())
