from __future__ import annotations

import time
from collections import deque
from datetime import datetime
from typing import Deque, Optional

from account import AccountService, AccountSnapshot
from config import TradingConfig
from market_data import MarketDataService
from orders import OrderService


class SamsungAutoTrader:
    def __init__(
        self,
        trading_config: TradingConfig,
        market_data: MarketDataService,
        account_service: AccountService,
        order_service: OrderService,
        logger,
    ):
        self.config = trading_config
        self.market_data = market_data
        self.account_service = account_service
        self.order_service = order_service
        self.logger = logger

        self.price_window: Deque[int] = deque(maxlen=self.config.disparity_window)
        self.entry_price: Optional[int] = None
        self.entry_time: Optional[float] = None
        self.last_balance_check_time: float = 0
        self.cached_snapshot: Optional[AccountSnapshot] = None

    def run(self) -> None:
        self.logger.info("Trader started. mock_only=True symbol=%s", self.config.symbol)

        while True:
            now = datetime.now().time()

            if now < self.config.trading_start:
                self.logger.info("Outside trading window. Waiting for market start.")
                time.sleep(30)
                continue

            if now >= self.config.trading_end:
                self.logger.info("Trading window ended. Trader stopped.")
                break

            try:
                self._run_once()
            except Exception as exc:
                self.logger.exception("Unexpected trading loop error: %s", exc)

            time.sleep(self.config.polling_interval_seconds)

    def _run_once(self) -> None:
        price = self.market_data.get_current_price(self.config.symbol)
        self.price_window.append(price)

        if len(self.price_window) < self.config.disparity_window:
            self.logger.info(
                "Collecting price window. current_count=%s required=%s",
                len(self.price_window),
                self.config.disparity_window,
            )
            return

        moving_average = sum(self.price_window) / len(self.price_window)
        disparity = price / moving_average * 100

        self.logger.info(
            "Disparity calculated. price=%s ma=%.2f disparity=%.3f",
            price,
            moving_average,
            disparity,
        )

        snapshot = self._get_snapshot_conservatively()
        holding_qty = snapshot.holding.quantity if snapshot.holding else 0

        if holding_qty > 0:
            self._maybe_sell(price, disparity, holding_qty)
        else:
            self._maybe_buy(price, disparity)

    def _maybe_buy(self, price: int, disparity: float) -> None:
        if disparity > self.config.buy_disparity_threshold:
            return

        self.logger.info(
            "Buy signal detected. disparity=%.3f threshold=%.3f",
            disparity,
            self.config.buy_disparity_threshold,
        )

        before = self.account_service.get_snapshot(self.config.symbol)
        before_qty = before.holding.quantity if before.holding else 0
        self.logger.info("Holdings before buy. quantity=%s", before_qty)

        self.order_service.buy_market(symbol=self.config.symbol, quantity=self.config.order_quantity)
        time.sleep(self.config.after_order_wait_seconds)

        after = self.account_service.get_snapshot(self.config.symbol)
        after_qty = after.holding.quantity if after.holding else 0
        self.logger.info("Holdings after buy. quantity=%s", after_qty)

        if after_qty > before_qty:
            self.logger.info("Buy execution seems to have occurred.")
            self.entry_price = price
            self.entry_time = time.time()
            self.cached_snapshot = after
            self.last_balance_check_time = time.time()
        else:
            self.logger.warning("Buy execution not confirmed.")

    def _maybe_sell(self, price: int, disparity: float, holding_qty: int) -> None:
        should_sell_by_disparity = disparity >= self.config.sell_disparity_threshold
        should_sell_by_profit = False
        should_sell_by_time = False

        if self.entry_price:
            return_rate = price / self.entry_price - 1
            should_sell_by_profit = (
                return_rate >= self.config.take_profit_rate
                or return_rate <= self.config.stop_loss_rate
            )
        else:
            return_rate = 0.0

        if self.entry_time:
            holding_seconds = time.time() - self.entry_time
            should_sell_by_time = holding_seconds >= self.config.max_holding_seconds
        else:
            holding_seconds = 0.0

        if not (should_sell_by_disparity or should_sell_by_profit or should_sell_by_time):
            return

        self.logger.info(
            "Sell signal detected. disparity=%.3f return_rate=%.5f holding_seconds=%.1f",
            disparity,
            return_rate,
            holding_seconds,
        )

        before = self.account_service.get_snapshot(self.config.symbol)
        before_qty = before.holding.quantity if before.holding else 0
        self.logger.info("Holdings before sell. quantity=%s", before_qty)

        sell_qty = min(holding_qty, self.config.order_quantity)
        self.order_service.sell_market(symbol=self.config.symbol, quantity=sell_qty)
        time.sleep(self.config.after_order_wait_seconds)

        after = self.account_service.get_snapshot(self.config.symbol)
        after_qty = after.holding.quantity if after.holding else 0
        self.logger.info("Holdings after sell. quantity=%s", after_qty)

        if after_qty < before_qty:
            self.logger.info("Sell execution seems to have occurred.")
            if after_qty == 0:
                self.entry_price = None
                self.entry_time = None
            self.cached_snapshot = after
            self.last_balance_check_time = time.time()
        else:
            self.logger.warning("Sell execution not confirmed.")

    def _get_snapshot_conservatively(self) -> AccountSnapshot:
        now = time.time()
        if (
            self.cached_snapshot is not None
            and now - self.last_balance_check_time < self.config.min_balance_check_interval_seconds
        ):
            return self.cached_snapshot

        snapshot = self.account_service.get_snapshot(self.config.symbol)
        self.cached_snapshot = snapshot
        self.last_balance_check_time = now
        return snapshot
