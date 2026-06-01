from __future__ import annotations

import logging
import time
from typing import Any, Literal

import requests

from auth import AuthManager
from config import Settings


HttpMethod = Literal["GET", "POST"]


class KISApiClient:
    """Small REST client with conservative retry handling."""

    def __init__(
        self,
        settings: Settings,
        auth_manager: AuthManager,
        logger: logging.Logger,
    ) -> None:
        self.settings = settings
        self.auth_manager = auth_manager
        self.logger = logger

    def request(
        self,
        method: HttpMethod,
        path: str,
        tr_id: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.settings.base_url}{path}"
        headers = self._headers(tr_id)

        for attempt in range(1, self.settings.max_retries + 2):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    timeout=self.settings.request_timeout_seconds,
                )

                if response.status_code == 429:
                    self.logger.warning("Rate limit received. attempt=%s", attempt)

                response.raise_for_status()
                data: dict[str, Any] = response.json()

                # KIS often uses rt_cd == "0" for success.
                if data.get("rt_cd") not in (None, "0"):
                    self.logger.error("KIS API error. tr_id=%s response=%s", tr_id, data)
                return data

            except (requests.Timeout, requests.ConnectionError) as exc:
                self.logger.warning(
                    "Temporary network error. tr_id=%s attempt=%s error=%s",
                    tr_id,
                    attempt,
                    exc,
                )
            except requests.HTTPError as exc:
                self.logger.error(
                    "HTTP error. tr_id=%s attempt=%s status=%s body=%s",
                    tr_id,
                    attempt,
                    getattr(exc.response, "status_code", None),
                    getattr(exc.response, "text", ""),
                )
                if attempt >= self.settings.max_retries + 1:
                    raise
            except requests.RequestException:
                self.logger.exception("Unexpected request error. tr_id=%s", tr_id)
                raise

            if attempt <= self.settings.max_retries:
                time.sleep(self.settings.retry_sleep_seconds)

        raise RuntimeError(f"Request failed after retries: {tr_id}")

    def _headers(self, tr_id: str) -> dict[str, str]:
        token = self.auth_manager.get_access_token()
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": self.settings.app_key,
            "appsecret": self.settings.app_secret,
            "tr_id": tr_id,
        }
