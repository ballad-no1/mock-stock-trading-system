from account import AccountService
from api_client import KisApiClient
from auth import AuthManager
from config import ApiConfig, TradingConfig, load_env_config
from logger import setup_logger
from market_data import MarketDataService
from orders import OrderService
from trader import SamsungAutoTrader


def main() -> None:
    logger = setup_logger()

    api_config = ApiConfig()
    trading_config = TradingConfig()
    env_config = load_env_config()

    auth_manager = AuthManager(
        api_config=api_config,
        env_config=env_config,
        logger=logger,
    )
    access_token = auth_manager.get_access_token()

    client = KisApiClient(
        api_config=api_config,
        env_config=env_config,
        access_token=access_token,
        logger=logger,
    )

    market_data = MarketDataService(client=client, api_config=api_config, logger=logger)
    account_service = AccountService(
        client=client,
        api_config=api_config,
        env_config=env_config,
        logger=logger,
    )
    order_service = OrderService(
        client=client,
        api_config=api_config,
        env_config=env_config,
        logger=logger,
    )

    trader = SamsungAutoTrader(
        trading_config=trading_config,
        market_data=market_data,
        account_service=account_service,
        order_service=order_service,
        logger=logger,
    )
    trader.run()


if __name__ == "__main__":
    main()
