"""Async FMP API client."""

import httpx

from fmp_py_client._base import BASE_URL, AsyncBaseClient
from fmp_py_client.api._bulk import BulkMixin
from fmp_py_client.api._calendar import CalendarMixin
from fmp_py_client.api._company import CompanyMixin
from fmp_py_client.api._crowdfunding import CrowdfundingMixin
from fmp_py_client.api._economics import EconomicsMixin
from fmp_py_client.api._esg import ESGMixin
from fmp_py_client.api._etf import ETFMixin
from fmp_py_client.api._financials import FinancialsMixin
from fmp_py_client.api._government import GovernmentMixin
from fmp_py_client.api._historical import HistoricalMixin
from fmp_py_client.api._insider import InsiderMixin
from fmp_py_client.api._market import MarketMixin
from fmp_py_client.api._mergers import MergersMixin
from fmp_py_client.api._metrics import MetricsMixin
from fmp_py_client.api._movers import MoversMixin
from fmp_py_client.api._news import NewsMixin
from fmp_py_client.api._quotes import QuotesMixin
from fmp_py_client.api._search import SearchMixin
from fmp_py_client.api._sec import SECMixin
from fmp_py_client.api._sector import SectorMixin
from fmp_py_client.api._technical import TechnicalMixin
from fmp_py_client.api._valuation import ValuationMixin


class AsyncFMPClient(
    SearchMixin,
    CompanyMixin,
    FinancialsMixin,
    MetricsMixin,
    QuotesMixin,
    HistoricalMixin,
    CalendarMixin,
    MarketMixin,
    NewsMixin,
    SectorMixin,
    MoversMixin,
    ValuationMixin,
    TechnicalMixin,
    ETFMixin,
    InsiderMixin,
    SECMixin,
    EconomicsMixin,
    GovernmentMixin,
    ESGMixin,
    CrowdfundingMixin,
    MergersMixin,
    BulkMixin,
    AsyncBaseClient,
):
    """Async FMP API client.

    Usage:
        async with AsyncFMPClient("your-api-key") as client:
            quotes = await client.quote("AAPL")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            httpx_client=httpx_client,
        )
