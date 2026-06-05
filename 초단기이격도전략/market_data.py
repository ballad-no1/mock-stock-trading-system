from __future__ import annotations

from api_client import KisApiClient
from config import ApiConfig


class MarketDataService:
    def __init__(self, client: KisApiClient, api_config: ApiConfig, logger):
        self.client = client
        self.api_config = api_config
        self.logger = logger

    def get_current_price(self, symbol: str) -> int:
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
        }

        data = self.client.get(
            path=self.api_config.price_path,
            tr_id=self.api_config.tr_id_current_price,
            params=params,
        )

        output = data.get("output", {})
        price_raw = output.get("stck_prpr")
        if price_raw is None:
            raise RuntimeError(f"Current price field not found: {data}")

        price = int(float(price_raw))
        self.logger.info("Current price. symbol=%s price=%s", symbol, price)
        return price
