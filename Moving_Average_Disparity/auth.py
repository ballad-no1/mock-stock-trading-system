from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Optional

import requests

from config import ApiConfig, EnvConfig


class AuthManager:
    """Issue and cache access token for same-day reuse."""

    def __init__(
        self,
        api_config: ApiConfig,
        env_config: EnvConfig,
        logger,
        cache_path: str = "token_cache.json",
    ):
        self.api_config = api_config
        self.env_config = env_config
        self.logger = logger
        self.cache_path = Path(cache_path)

    def get_access_token(self) -> str:
        cached = self._load_cached_token()
        if cached:
            self.logger.info("Reusing cached access token for today.")
            return cached

        self.logger.info("Requesting new access token.")
        token = self._request_new_token()
        self._save_token(token)
        return token

    def _load_cached_token(self) -> Optional[str]:
        if not self.cache_path.exists():
            return None

        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

        if data.get("date") != date.today().isoformat():
            return None

        token = data.get("access_token")
        return token if token else None

    def _save_token(self, token: str) -> None:
        payload = {
            "date": date.today().isoformat(),
            "access_token": token,
        }
        self.cache_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _request_new_token(self) -> str:
        url = self.api_config.base_url + self.api_config.token_path
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.env_config.appkey,
            "appsecret": self.env_config.appsecret,
        }

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()

        data = response.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"Access token not found in response: {data}")

        return token
