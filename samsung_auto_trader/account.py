from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from api_client import KISApiClient
from config import Settings


@dataclass(frozen=True)
class Holding:
    symbol: str
    name: str
    quantity: int
    average_price: int | None = None


@dataclass(frozen=True)
class AccountSnapshot:
    holdings: list[Holding]
    available_cash: int | None
    raw: dict[str, Any]

    def quantity_of(self, symbol: str) -> int:
        for holding in self.holdings:
            if holding.symbol == symbol:
                return holding.quantity
        return 0


class AccountService:
    def __init__(
        self,
        client: KISApiClient,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self.client = client
        self.settings = settings
        self.logger = logger

    def get_balance(self) -> AccountSnapshot:
        data = self.client.request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            self.settings.tr_id_inquire_balance,
            params={
                "CANO": self.settings.cano,
                "ACNT_PRDT_CD": self.settings.acnt_prdt_cd,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
        )

        holdings = self._parse_holdings(data)
        available_cash = self._parse_available_cash(data)

        samsung_qty = next(
            (holding.quantity for holding in holdings if holding.symbol == self.settings.symbol),
            0,
        )
        self.logger.info(
            "Holdings checked. total_positions=%s %s_qty=%s available_cash=%s",
            len(holdings),
            self.settings.symbol,
            samsung_qty,
            available_cash,
        )
        return AccountSnapshot(
            holdings=holdings,
            available_cash=available_cash,
            raw=data,
        )

    def _parse_holdings(self, data: dict[str, Any]) -> list[Holding]:
        output1 = data.get("output1") or []
        holdings: list[Holding] = []

        for item in output1:
            symbol = str(item.get("pdno", "")).strip()
            quantity = self._safe_int(item.get("hldg_qty"))
            if not symbol or quantity <= 0:
                continue

            holdings.append(
                Holding(
                    symbol=symbol,
                    name=str(item.get("prdt_name", "")).strip(),
                    quantity=quantity,
                    average_price=self._safe_int_or_none(item.get("pchs_avg_pric")),
                )
            )

        return holdings

    def _parse_available_cash(self, data: dict[str, Any]) -> int | None:
        # KIS balance output fields can differ by API version/account type.
        # These are common candidate names; keep isolated for easy adjustment.
        output2 = data.get("output2") or []
        if isinstance(output2, list) and output2:
            candidates = [
                "dnca_tot_amt",
                "nass_amt",
                "scts_evlu_amt",
                "tot_evlu_amt",
                "ord_psbl_cash",
            ]
            for key in candidates:
                if key in output2[0]:
                    return self._safe_int_or_none(output2[0].get(key))
        return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _safe_int_or_none(value: Any) -> int | None:
        try:
            return int(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return None
