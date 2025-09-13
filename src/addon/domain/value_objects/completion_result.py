import datetime


class CompletionResult:
    """Represents the result of an LLM text completion operation.

    This value object encapsulates the outcome of calling an LLM service
    (such as OpenAI or vLLM) to generate text based on a prompt.

    Args:
        text: The generated text content from the LLM
        source: The LLM service or model that generated the completion
        timestamp: When the completion was generated
    """

    def __init__(
        self, text: str, source: str, timestamp: datetime.datetime
    ) -> None:
        self.text = text
        self.source = source
        self.timestamp = timestamp
