import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    _loaded = False

    def __init__(self):
        self._api_key: str | None = None
        self._base_url: str = "https://api.dooray.com"

    def load(self) -> None:
        if Config._loaded:
            return

        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        self._api_key = os.getenv("DOORAY_API_KEY")

        base_url = os.getenv("DOORAY_BASE_URL")
        if base_url:
            self._base_url = base_url.rstrip("/")

        Config._loaded = True

    @property
    def api_key(self) -> str | None:
        return self._api_key

    @property
    def base_url(self) -> str:
        return self._base_url


config = Config()
