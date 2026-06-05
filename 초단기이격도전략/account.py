from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from api_client import KisApiClient
from config import ApiConfig, EnvConfig


@dataclass
class Holding:
    symbol: str
    quantity: int
    average_price: float


@dataclass
class AccountSnapshot:
    cash_available: int
    holding: Optional[Holding]


class AccountService:
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

    def get_snapshot(self, symbol: str) -> AccountSnapshot:
        params: Dict[str, Any] = {
            "CANO": self.env_config.cano,
            "ACNT_PRDT_CD": self.env_config.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        data = self.client.get(
            path=self.api_config.balance_path,
            tr_id=self.api_config.tr_id_balance_mock,
            params=params,
        )

        holding = self._parse_holding(data, symbol)
        cash_available = self._parse_cash_available(data)

        self.logger.info(
            "Account snapshot. symbol=%s holding_qty=%s avg_price=%s cash_available=%s",
            symbol,
            holding.quantity if holding else 0,
            holding.average_price if holding else 0,
            cash_available,
        )

        return AccountSnapshot(cash_available=cash_available, holding=holding)

    def _parse_holding(self, data: Dict[str, Any], symbol: str) -> Optional[Holding]:
        output1 = data.get("output1", [])
        for row in output1:
            code = row.get("pdno")
            if code != symbol:
                continue

            quantity = int(float(row.get("hldg_qty", 0)))
            average_price = float(row.get("pchs_avg_pric", 0))
            if quantity <= 0:
                return None

            return Holding(symbol=symbol, quantity=quantity, average_price=average_price)

        return None

    def _parse_cash_available(self, data: Dict[str, Any]) -> int:
        output2 = data.get("output2", [])
        if isinstance(output2, list) and output2:
            row = output2[0]
        elif isinstance(output2, dict):
            row = output2
        else:
            return 0

        raw = row.get("dnca_tot_amt") or row.get("ord_psbl_cash") or row.get("nass_amt") or 0
        return int(float(raw))
