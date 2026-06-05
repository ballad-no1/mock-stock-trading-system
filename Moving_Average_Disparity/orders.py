from __future__ import annotations

from typing import Any, Dict

from api_client import KisApiClient
from config import ApiConfig, EnvConfig


class OrderService:
    def __init__(
        self,
        client: KisApiClient,
        api_config: ApiConfig,
        env_config: EnvConfig,
        logger,
    ):
        self.client = client
        self.api_config = api_config
        self.env_config = env_config
        self.logger = logger

    def buy_market(self, symbol: str, quantity: int) -> Dict[str, Any]:
        self.logger.info("Buy order request. symbol=%s quantity=%s", symbol, quantity)
        payload = self._base_order_payload(symbol=symbol, quantity=quantity, order_division="01", price="0")
        return self.client.post(
            path=self.api_config.order_cash_path,
            tr_id=self.api_config.tr_id_buy_mock,
            payload=payload,
        )

    def sell_market(self, symbol: str, quantity: int) -> Dict[str, Any]:
        self.logger.info("Sell order request. symbol=%s quantity=%s", symbol, quantity)
        payload = self._base_order_payload(symbol=symbol, quantity=quantity, order_division="01", price="0")
        return self.client.post(
            path=self.api_config.order_cash_path,
            tr_id=self.api_config.tr_id_sell_mock,
            payload=payload,
        )

    def _base_order_payload(
        self,
        symbol: str,
        quantity: int,
        order_division: str,
        price: str,
    ) -> Dict[str, Any]:
        return {
            "CANO": self.env_config.cano,
            "ACNT_PRDT_CD": self.env_config.acnt_prdt_cd,
            "PDNO": symbol,
            "ORD_DVSN": order_division,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": price,
        }
