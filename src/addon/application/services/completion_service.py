from datetime import datetime

from anki.notes import Note

from ...domain.models.completion_result import CompletionResult
from ...infrastructure.openai import OpenAIClient


class CompletionService:
    def __init__(self, client: OpenAIClient):
        self._client = client

    def generate(self, prompt: str) -> CompletionResult:
        raw_response = self._client.run(prompt)

        # Transform the raw response into a domain object
        completion = CompletionResult(
            text=raw_response, source="openai", timestamp=datetime.now()
        )
        return completion


def format_note(note: Note, completion_service: CompletionService) -> Note:
    for field_name in note.keys():
        ctx = note[field_name]
        prompt = f"Convert this text to lowercase: {ctx}"
        transformed_content = completion_service.generate(prompt=prompt)
        note[field_name] = transformed_content.text
    result = note
    return result
