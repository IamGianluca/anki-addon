import datetime


class CompletionResult:
    def __init__(self, text: str, source: str, timestamp: datetime.datetime) -> None:
        self.text = text
        self.source = source
        self.timestamp = timestamp
