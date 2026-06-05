from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class ApiConfig:
    """Korea Investment Open API configuration for mock trading."""

    base_url: str = "https://openapivts.koreainvestment.com:29443"
    token_path: str = "/oauth2/tokenP"

    price_path: str = "/uapi/domestic-stock/v1/quotations/inquire-price"
    balance_path: str = "/uapi/domestic-stock/v1/trading/inquire-balance"
    order_cash_path: str = "/uapi/domestic-stock/v1/trading/order-cash"

    # TR IDs for mock trading. If the API document shows different values,
    # edit only this section.
    tr_id_current_price: str = "FHKST01010100"
    tr_id_balance_mock: str = "VTTC8434R"
    tr_id_buy_mock: str = "VTTC0802U"
    tr_id_sell_mock: str = "VTTC0801U"

    customer_type: str = "P"


@dataclass(frozen=True)
class TradingConfig:
    """Trading parameters. Keep these conservative for mock trading limits."""

    symbol: str = "005930"
    stock_name: str = "Samsung Electronics"

    trading_start: time = time(9, 10)
    trading_end: time = time(15, 30)

    disparity_window: int = 20
    buy_disparity_threshold: float = 99.6
    sell_disparity_threshold: float = 100.2

    take_profit_rate: float = 0.002      # +0.2%
    stop_loss_rate: float = -0.0015      # -0.15%
    max_holding_seconds: int = 60

    # Mock trading rate limit is strict. Keep this large enough.
    polling_interval_seconds: int = 10
    after_order_wait_seconds: int = 5
    min_balance_check_interval_seconds: int = 30

    order_quantity: int = 1


@dataclass(frozen=True)
class EnvConfig:
    appkey: str
    appsecret: str
    account: str

    @property
    def cano(self) -> str:
        cleaned = self.account.replace("-", "").strip()
        return cleaned[:8]

    @property
    def acnt_prdt_cd(self) -> str:
        cleaned = self.account.replace("-", "").strip()
        return cleaned[8:10]


def load_env_config() -> EnvConfig:
    appkey = os.getenv("GH_APPKEY")
    appsecret = os.getenv("GH_APPSECRET")
    account = os.getenv("GH_ACCOUNT")

    missing = [
        key
        for key, value in {
            "GH_APPKEY": appkey,
            "GH_APPSECRET": appsecret,
            "GH_ACCOUNT": account,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    return EnvConfig(
        appkey=appkey.strip(),
        appsecret=appsecret.strip(),
        account=account.strip(),
    )
