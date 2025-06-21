from datetime import datetime

from ...domain.value_objects.completion_result import CompletionResult
from ...infrastructure.external_services.openai import OpenAIClient


class CompletionService:
    def __init__(self, client: OpenAIClient):
        self._client = client

    def generate(self, prompt: str, **kwargs) -> CompletionResult:
        raw_response = self._client.run(prompt, **kwargs)

        # Transform the raw response into a domain object
        completion = CompletionResult(
            text=raw_response, source="vllm", timestamp=datetime.now()
        )
        return completion
