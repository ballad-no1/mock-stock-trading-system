from __future__ import annotations

import logging

from api_client import KISApiClient
from config import Settings


class MarketDataService:
    def __init__(
        self,
        client: KISApiClient,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.client = client
        self.settings = settings
        self.logger = logger

    def get_current_price(self, symbol: str | None = None) -> int:
        symbol = symbol or self.settings.symbol
        data = self.client.request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            self.settings.tr_id_current_price,
            params={
                "FID_COND_MRKT_DIV_CODE": self.settings.market_div_code,
                "FID_INPUT_ISCD": symbol,
            },
        )

        output = data.get("output") or {}
        price_raw = output.get("stck_prpr")
        if price_raw is None:
            self.logger.error("Current price field missing. response=%s", data)
            raise RuntimeError("Current price field stck_prpr missing")

        price = int(str(price_raw).replace(",", ""))
        self.logger.info("Current price. symbol=%s price=%s", symbol, price)
        return price
