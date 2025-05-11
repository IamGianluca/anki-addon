import os

from aqt.main import AnkiQt

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
