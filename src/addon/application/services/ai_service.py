from datetime import datetime
from addon.domain.models.completion_result import CompletionResult
from addon.infrastructure.openai import OpenAIClient


class AICompletionService:
    def __init__(self, client: OpenAIClient):
        self._client = client

    def generate_completion(self, prompt: str) -> CompletionResult:
        raw_response = self._client.run(prompt)

        # Transform the raw response into a domain object
        completion = CompletionResult(
            text=raw_response, source="openai", timestamp=datetime.now()
        )
        return completion
