from __future__ import annotations

import logging
import time
from datetime import datetime

from account import AccountService, AccountSnapshot
from config import Settings
from market_data import MarketDataService
from orders import OrderService


class SamsungAutoTrader:
    def __init__(
        self,
        settings: Settings,
        market_data: MarketDataService,
        account: AccountService,
        orders: OrderService,
        logger: logging.Logger,
    ) -> None:
        self.settings = settings
        self.market_data = market_data
        self.account = account
        self.orders = orders
        self.logger = logger

    def run_forever(self) -> None:
        self.logger.info("Trader started. mock_only=True symbol=%s", self.settings.symbol)

        while True:
            now = datetime.now().time()

            if now < self.settings.trading_start:
                self.logger.info(
                    "Outside trading window. Waiting. start=%s now=%s",
                    self.settings.trading_start,
                    now.replace(microsecond=0),
                )
                time.sleep(min(self.settings.poll_interval_seconds, 60))
                continue

            if now >= self.settings.trading_end:
                self.logger.info("Trading window ended. end=%s now=%s", self.settings.trading_end, now)
                break

            self.run_once()
            time.sleep(self.settings.poll_interval_seconds)

        self.logger.info("Trader stopped automatically after trading window.")

    def run_once(self) -> None:
        symbol = self.settings.symbol

        try:
            current_price = self.market_data.get_current_price(symbol)
            before = self.account.get_balance()
            self._log_snapshot("before_order", before)

            buy_price = max(current_price - self.settings.buy_price_offset, 1)
            sell_price = current_price + self.settings.sell_price_offset

            buy_result = self.orders.buy_limit(
                symbol=symbol,
                quantity=self.settings.order_quantity,
                price=buy_price,
            )
            after_buy = self.account.get_balance()
            self._log_execution_check("BUY", before, after_buy, symbol)
            self._log_snapshot("after_buy", after_buy)

            # Do not call price again. Reuse the price checked at the beginning
            # to reduce mock API usage.
            sell_result = self.orders.sell_limit(
                symbol=symbol,
                quantity=self.settings.order_quantity,
                price=sell_price,
            )
            after_sell = self.account.get_balance()
            self._log_execution_check("SELL", after_buy, after_sell, symbol)
            self._log_snapshot("after_sell", after_sell)

            if not buy_result.success or not sell_result.success:
                self.logger.warning(
                    "At least one order request was not successful. buy_success=%s sell_success=%s",
                    buy_result.success,
                    sell_result.success,
                )

        except Exception:
            self.logger.exception("Trading cycle failed. Skipping this cycle.")

    def _log_snapshot(self, label: str, snapshot: AccountSnapshot) -> None:
        qty = snapshot.quantity_of(self.settings.symbol)
        self.logger.info(
            "Snapshot %s. %s_qty=%s available_cash=%s",
            label,
            self.settings.symbol,
            qty,
            snapshot.available_cash,
        )

    def _log_execution_check(
        self,
        side: str,
        before: AccountSnapshot,
        after: AccountSnapshot,
        symbol: str,
    ) -> None:
        before_qty = before.quantity_of(symbol)
        after_qty = after.quantity_of(symbol)

        if side == "BUY":
            executed = after_qty > before_qty
        else:
            executed = after_qty < before_qty

        self.logger.info(
            "Execution check. side=%s before_qty=%s after_qty=%s seems_executed=%s",
            side,
            before_qty,
            after_qty,
            executed,
        )
