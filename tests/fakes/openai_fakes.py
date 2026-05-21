"""Test doubles for OpenAI-compatible HTTP interactions."""

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient


class FakeOpenAIClient:
    """Factory that builds an OpenAIClient with stubbed HTTP responses.

    Accepts plain string responses and formats them into the OpenAI API
    response shape that OpenAIClient expects.
    """

    @staticmethod
    def create(config: AddonConfig, responses: list[str]) -> OpenAIClient:
        is_chat = "chat/completions" in config.url

        def _format_response_as_openai_api(response: str) -> dict:
            if is_chat:
                return {
                    "choices": [
                        {
                            "message": {"content": response},
                            "index": 0,
                            "finish_reason": "length",
                        }
                    ],
                    "model": "null-model",
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 1,
                        "total_tokens": 1,
                    },
                }
            else:
                return {
                    "choices": [
                        {
                            "text": response,
                            "index": 0,
                            "finish_reason": "length",
                        }
                    ],
                    "model": "null-model",
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 1,
                        "total_tokens": 1,
                    },
                }

        formatted = [_format_response_as_openai_api(r) for r in responses]
        return OpenAIClient(config, StubbedRequests(formatted))


class StubbedRequests:
    """Test double that replaces the requests module for deterministic
    testing.

    Records all HTTP calls made during testing and returns pre-configured
    responses instead of making actual network requests.
    """

    def __init__(self, responses: list) -> None:
        self._responses = responses
        self._calls: list[dict] = []

    def post(self, url, json=None) -> "StubbedResponse":
        self._calls.append({"url": url, "json": json})
        return StubbedResponse(self._responses)


class StubbedResponse:
    """Mock HTTP response object that mimics the requests library response.

    Provides the same interface as requests.Response.json() but returns
    pre-configured data instead of parsing actual HTTP response content.
    Supports both sequential responses (list) and repeated responses (single
    value).
    """

    def __init__(self, responses):
        self._response = self._get_next_response(responses)
        self.status_code = 200

    def json(self) -> dict:
        return self._response

    @staticmethod
    def _get_next_response(responses) -> dict:
        if isinstance(responses, list):
            if not responses:
                raise Exception(
                    "No more responses configured in fake OpenAIClient"
                )
            return responses.pop(0)
        else:
            return responses
