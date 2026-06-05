from __future__ import annotations

import time
from typing import Any, Dict

import requests

from config import ApiConfig, EnvConfig


class KisApiClient:
    """Small REST client with simple retry and rate-limit backoff."""

    def __init__(
        self,
        api_config: ApiConfig,
        env_config: EnvConfig,
        access_token: str,
        logger,
    ):
        self.api_config = api_config
        self.env_config = env_config
        self.access_token = access_token
        self.logger = logger

    def _headers(self, tr_id: str) -> Dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.env_config.appkey,
            "appsecret": self.env_config.appsecret,
            "tr_id": tr_id,
            "custtype": self.api_config.customer_type,
        }

    def get(
        self,
        path: str,
        tr_id: str,
        params: Dict[str, Any],
        retries: int = 2,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        url = self.api_config.base_url + path

        for attempt in range(1, retries + 2):
            try:
                response = requests.get(
                    url,
                    headers=self._headers(tr_id),
                    params=params,
                    timeout=timeout,
                )
                return self._handle_response(response, tr_id, attempt)
            except requests.RequestException as exc:
                self.logger.error(
                    "GET request failed. tr_id=%s attempt=%s error=%s",
                    tr_id,
                    attempt,
                    exc,
                )
                if attempt > retries:
                    raise
                time.sleep(2.0 * attempt)

        raise RuntimeError("Unexpected GET failure.")

    def post(
        self,
        path: str,
        tr_id: str,
        payload: Dict[str, Any],
        retries: int = 1,
        timeout: int = 5,
    ) -> Dict[str, Any]:
        url = self.api_config.base_url + path

        for attempt in range(1, retries + 2):
            try:
                response = requests.post(
                    url,
                    headers=self._headers(tr_id),
                    json=payload,
                    timeout=timeout,
                )
                return self._handle_response(response, tr_id, attempt)
            except requests.RequestException as exc:
                self.logger.error(
                    "POST request failed. tr_id=%s attempt=%s error=%s",
                    tr_id,
                    attempt,
                    exc,
                )
                if attempt > retries:
                    raise
                time.sleep(2.0 * attempt)

        raise RuntimeError("Unexpected POST failure.")

    def _handle_response(self, response: requests.Response, tr_id: str, attempt: int) -> Dict[str, Any]:
        if response.status_code >= 400:
            self.logger.error(
                "HTTP error. tr_id=%s attempt=%s status=%s body=%s",
                tr_id,
                attempt,
                response.status_code,
                response.text,
            )
            response.raise_for_status()

        data = response.json()

        # Korea Investment often returns rt_cd='1' even with HTTP 200 for business errors.
        if data.get("rt_cd") == "1":
            msg = str(data.get("msg1", ""))
            code = str(data.get("msg_cd", ""))
            self.logger.error(
                "API business error. tr_id=%s attempt=%s msg_cd=%s msg=%s body=%s",
                tr_id,
                attempt,
                code,
                msg,
                data,
            )
            if "초당 거래건수" in msg or code == "EGW00201":
                time.sleep(3)
            raise RuntimeError(f"API business error: {code} {msg}")

        return data
