import os

from aqt.main import AnkiQt
import requests

from ..utils import ensure_config


class AddonConfig:
    """An infrastructure wrapper for Anki's configuration system."""

    @staticmethod
    def create(mw: AnkiQt):
        c: dict = ensure_config(mw.addonManager.getConfig("anki-addon"))
        config = dict()
        config["host"] = c.get("openai_host")
        config["port"] = c.get("openai_port")
        config["model_name"] = c.get("openai_model")
        return AddonConfig(config)

    @staticmethod
    def create_nullable():
        config = dict()
        config["host"] = os.environ.get("OPENAI_HOST")
        config["port"] = os.environ.get("OPENAI_PORT")
        config["model_name"] = os.environ.get("OPENAI_MODEL")
        return AddonConfig(config)

    def __init__(self, config) -> None:
        self.url = f"http://{config['host']}:{config['port']}/v1/completions"
        self.model_name = config["model_name"]


class OpenAIClient:
    @staticmethod
    def create(config: AddonConfig):
        return OpenAIClient(config, requests)

    @staticmethod
    def create_nullable(config: AddonConfig, responses: list[str]):
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

    def __init__(self, config, http_client) -> None:
        self._http_client = http_client
        self.url = config.url
        self.model = config.model_name

    def run(self, prompt: str) -> str:
        data = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 2,
            "temperature": 0,
        }

        response = self._http_client.post(self.url, json=data)
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
