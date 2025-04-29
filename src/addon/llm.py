import os
import requests


class LLM:
    def __init__(self) -> None:
        host = os.environ["OPENAI_HOST"]
        port = os.environ["OPENAI_PORT"]
        self.url = f"http://{host}:{port}/v1/completions"
        self.model = os.environ["OPENAI_MODEL"]

    def run(self, prompt: str) -> str:
        data = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 2,
            "temperature": 0,
        }

        response = requests.post(self.url, json=data)
        return response.json()["choices"][0]["text"]
