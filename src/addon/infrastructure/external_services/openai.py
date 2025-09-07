import requests
import requests.exceptions

from ...infrastructure.configuration.settings import AddonConfig


class OpenAIClient:
    """Adapter for OpenAI compatible inference servers (e.g., vLLM)."""

    @staticmethod
    def create(config: AddonConfig):
        return OpenAIClient(config, requests)

    @staticmethod
    def create_null(config: AddonConfig, responses: list[str]):
        def _format_response_as_openai_api(response: str) -> dict:
            return {
                "choices": [
                    {"text": response, "index": 0, "finish_reason": "length"}
                ],
                "model": "null-model",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 1,
                    "total_tokens": 1,
                },
            }

        r = [_format_response_as_openai_api(res) for res in responses]
        return OpenAIClient(config, OpenAIClient.StubbedRequests(r))

    def __init__(self, config: AddonConfig, http_client) -> None:
        self._http_client = http_client
        self.url = config.url
        self.model = config.model_name

    def run(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0,
        }
        if kwargs:
            payload.update(kwargs)

        try:
            response = self._http_client.post(self.url, json=payload)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Cannot reach LLM server at {self.url}. "
                "Check if the inference server is running."
            ) from e
        return response.json()["choices"][0]["text"]

    class StubbedRequests:
        def __init__(self, responses: list):
            self._responses = responses
            self._calls = []

        def post(self, url, json=None):
            self._calls.append({"url": url, "json": json})
            return OpenAIClient.StubbedResponse(self._responses)

    class StubbedResponse:
        def __init__(self, responses):
            # Get the next response from the configured list
            self._response = self._get_next_response(responses)

        def json(self):
            return self._response

        @staticmethod
        def _get_next_response(responses):
            if isinstance(responses, list):
                # If it's a list, pop the next response
                if not responses:
                    raise Exception(
                        "No more responses configured in nulled OpenAIClient"
                    )
                return responses.pop(0)
            else:
                # If it's a single value, always return that
                return responses

    def track_calls(self):
        """Output Tracking - track what calls were made to the HTTP client"""
        if hasattr(self._http_client, "_calls"):
            return self._http_client._calls
        return []
