import os

import requests


class OpenAIClient:
    @staticmethod
    def create():
        return OpenAIClient(requests)

    @staticmethod
    def create_nullable(responses: list[str]):
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
        return OpenAIClient(OpenAIClient.StubbedRequests(r))

    def __init__(self, http_client) -> None:
        self._http_client = http_client
        host = os.environ.get("OPENAI_HOST")
        port = os.environ.get("OPENAI_PORT")
        self.url = f"http://{host}:{port}/v1/completions"
        self.model = os.environ.get("OPENAI_MODEL")

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
