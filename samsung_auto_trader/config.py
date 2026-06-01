from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """
    Mock-trading-only settings.

    Required GitHub Codespaces / environment variables:
      - GH_ACCOUNT: mock account number. Accepts "12345678-01", "1234567801", or "12345678"
      - GH_APPKEY
      - GH_APPSECRET

    If GH_ACCOUNT has only 8 digits, account product code defaults to "01".
    """
    account: str
    app_key: str
    app_secret: str

    # Mock trading base URL
    base_url: str = "https://openapivts.koreainvestment.com:29443"

    # Target: Samsung Electronics
    symbol: str = "005930"
    market_div_code: str = "J"

    # Trading behavior
    buy_price_offset: int = 1_000
    sell_price_offset: int = 1_000
    order_quantity: int = 1

    # Conservative polling for mock environment
    poll_interval_seconds: int = 180
    request_timeout_seconds: int = 10
    max_retries: int = 2
    retry_sleep_seconds: int = 1

    # KST trading window
    trading_start: time = time(9, 10)
    trading_end: time = time(15, 30)

    # Local files
    token_cache_path: Path = Path("token_cache.json")
    log_file_path: Path = Path("logs/trader.log")

    # Transaction IDs. Keep them isolated here so they are easy to edit
    # if Korea Investment changes field names/TR IDs.
    tr_id_current_price: str = "FHKST01010100"
    tr_id_inquire_balance: str = "VTTC8434R"
    tr_id_buy_order: str = "VTTC0802U"
    tr_id_sell_order: str = "VTTC0801U"

    # Domestic stock exchange division code. Commonly used: "01" for KRX.
    order_exchange_code: str = "01"

    @property
    def cano(self) -> str:
        cleaned = self.account.replace("-", "").strip()
        if len(cleaned) < 8:
            raise ValueError("GH_ACCOUNT must contain at least the first 8 account digits.")
        return cleaned[:8]

    @property
    def acnt_prdt_cd(self) -> str:
        cleaned = self.account.replace("-", "").strip()
        if len(cleaned) >= 10:
            return cleaned[8:10]
        return "01"


def load_settings() -> Settings:
    account = os.getenv("GH_ACCOUNT", "").strip()
    app_key = os.getenv("GH_APPKEY", "").strip()
    app_secret = os.getenv("GH_APPSECRET", "").strip()

    missing = [
        name
        for name, value in {
            "GH_ACCOUNT": account,
            "GH_APPKEY": app_key,
            "GH_APPSECRET": app_secret,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(account=account, app_key=app_key, app_secret=app_secret)
