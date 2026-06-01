from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from config import Settings


@dataclass(frozen=True)
class Token:
    access_token: str
    issued_date: str


class AuthManager:
    """
    Issues and reuses a REST access token.

    The access token is cached by calendar date to avoid unnecessary token issuance.
    If the token fails later, delete token_cache.json and rerun.
    """

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def get_access_token(self) -> str:
        cached = self._load_cached_token()
        today = date.today().isoformat()

        if cached and cached.issued_date == today:
            self.logger.info("Reusing cached access token for %s", today)
            return cached.access_token

        self.logger.info("No same-day token found. Requesting new access token.")
        token = self._request_new_token()
        self._save_token(token)
        return token.access_token

    def _load_cached_token(self) -> Token | None:
        path = self.settings.token_cache_path
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            access_token = data.get("access_token")
            issued_date = data.get("issued_date")
            if access_token and issued_date:
                return Token(access_token=access_token, issued_date=issued_date)
        except (OSError, json.JSONDecodeError) as exc:
            self.logger.warning("Could not read token cache: %s", exc)

        return None

    def _save_token(self, token: Token) -> None:
        path = self.settings.token_cache_path
        data = {
            "access_token": token.access_token,
            "issued_date": token.issued_date,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("Saved access token cache to %s", path)

    def _request_new_token(self) -> Token:
        url = f"{self.settings.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.settings.app_key,
            "appsecret": self.settings.app_secret,
        }

        try:
            response = requests.post(
                url,
                headers={"content-type": "application/json"},
                json=payload,
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            self.logger.exception("Token request failed")
            raise RuntimeError("Failed to request access token") from exc

        data: dict[str, Any] = response.json()
        access_token = data.get("access_token")
        if not access_token:
            self.logger.error("Token response did not contain access_token: %s", data)
            raise RuntimeError("Token response did not contain access_token")

        self.logger.info("New access token issued")
        return Token(access_token=access_token, issued_date=date.today().isoformat())
