from __future__ import annotations

from account import AccountService
from api_client import KISApiClient
from auth import AuthManager
from config import load_settings
from logger import setup_logger
from market_data import MarketDataService
from orders import OrderService
from trader import SamsungAutoTrader


def main() -> None:
    settings = load_settings()
    logger = setup_logger(settings.log_file_path)

    auth_manager = AuthManager(settings=settings, logger=logger)
    client = KISApiClient(settings=settings, auth_manager=auth_manager, logger=logger)

    market_data = MarketDataService(client=client, settings=settings, logger=logger)
    account = AccountService(client=client, settings=settings, logger=logger)
    orders = OrderService(client=client, settings=settings, logger=logger)

    trader = SamsungAutoTrader(
        settings=settings,
        market_data=market_data,
        account=account,
        orders=orders,
        logger=logger,
    )
    trader.run_forever()


if __name__ == "__main__":
    main()
