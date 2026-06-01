from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from api_client import KISApiClient
from config import Settings


Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class OrderResult:
    side: Side
    symbol: str
    quantity: int
    price: int
    success: bool
    order_no: str | None
    raw: dict[str, Any]


class OrderService:
    def __init__(
        self,
        client: KISApiClient,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.client = client
        self.settings = settings
        self.logger = logger

    def buy_limit(self, symbol: str, quantity: int, price: int) -> OrderResult:
        self.logger.info("Buy order request. symbol=%s qty=%s price=%s", symbol, quantity, price)
        return self._submit_order("BUY", symbol, quantity, price)

    def sell_limit(self, symbol: str, quantity: int, price: int) -> OrderResult:
        self.logger.info("Sell order request. symbol=%s qty=%s price=%s", symbol, quantity, price)
        return self._submit_order("SELL", symbol, quantity, price)

    def _submit_order(
        self,
        side: Side,
        symbol: str,
        quantity: int,
        price: int,
    ) -> OrderResult:
        tr_id = (
            self.settings.tr_id_buy_order
            if side == "BUY"
            else self.settings.tr_id_sell_order
        )

        # ORD_DVSN "00" is commonly used for limit orders.
        data = self.client.request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-cash",
            tr_id,
            json_body={
                "CANO": self.settings.cano,
                "ACNT_PRDT_CD": self.settings.acnt_prdt_cd,
                "PDNO": symbol,
                "ORD_DVSN": "00",
                "ORD_QTY": str(quantity),
                "ORD_UNPR": str(price),
            },
        )

        output = data.get("output") or {}
        order_no = output.get("ODNO") or output.get("odno")
        success = data.get("rt_cd") == "0"

        self.logger.info(
            "%s order response. success=%s order_no=%s response=%s",
            side,
            success,
            order_no,
            data,
        )

        return OrderResult(
            side=side,
            symbol=symbol,
            quantity=quantity,
            price=price,
            success=success,
            order_no=order_no,
            raw=data,
        )
