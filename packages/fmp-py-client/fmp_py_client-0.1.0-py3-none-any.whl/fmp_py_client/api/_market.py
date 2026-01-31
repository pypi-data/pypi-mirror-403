"""Market info and lists API endpoints."""

from fmp_py_client._types import JSONArray


class MarketMixin:
    """Market info, lists, and index constituent endpoints."""

    async def stock_list(self) -> JSONArray:
        """Get list of all stock symbols."""
        return await self._request("stock-list")  # type: ignore[attr-defined]

    async def financial_statement_symbol_list(self) -> JSONArray:
        """Get list of symbols with financial statements."""
        return await self._request("financial-statement-symbol-list")  # type: ignore[attr-defined]

    async def cik_list(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get list of CIK numbers."""
        return await self._request(  # type: ignore[attr-defined]
            "cik-list",
            params={"page": page, "limit": limit},
        )

    async def symbol_change(self) -> JSONArray:
        """Get list of symbol changes."""
        return await self._request("symbol-change")  # type: ignore[attr-defined]

    async def etf_list(self) -> JSONArray:
        """Get list of ETF symbols."""
        return await self._request("etf-list")  # type: ignore[attr-defined]

    async def actively_trading_list(self) -> JSONArray:
        """Get list of actively trading symbols."""
        return await self._request("actively-trading-list")  # type: ignore[attr-defined]

    async def delisted_companies(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get list of delisted companies."""
        return await self._request(  # type: ignore[attr-defined]
            "delisted-companies",
            params={"page": page, "limit": limit},
        )

    async def available_exchanges(self) -> JSONArray:
        """Get list of available exchanges."""
        return await self._request("available-exchanges")  # type: ignore[attr-defined]

    async def available_sectors(self) -> JSONArray:
        """Get list of available sectors."""
        return await self._request("available-sectors")  # type: ignore[attr-defined]

    async def available_industries(self) -> JSONArray:
        """Get list of available industries."""
        return await self._request("available-industries")  # type: ignore[attr-defined]

    async def available_countries(self) -> JSONArray:
        """Get list of available countries."""
        return await self._request("available-countries")  # type: ignore[attr-defined]

    async def index_list(self) -> JSONArray:
        """Get list of market indexes."""
        return await self._request("index-list")  # type: ignore[attr-defined]

    async def sp500_constituent(self) -> JSONArray:
        """Get S&P 500 constituents."""
        return await self._request("sp500-constituent")  # type: ignore[attr-defined]

    async def nasdaq_constituent(self) -> JSONArray:
        """Get Nasdaq constituents."""
        return await self._request("nasdaq-constituent")  # type: ignore[attr-defined]

    async def dowjones_constituent(self) -> JSONArray:
        """Get Dow Jones constituents."""
        return await self._request("dowjones-constituent")  # type: ignore[attr-defined]

    async def historical_sp500_constituent(self) -> JSONArray:
        """Get historical S&P 500 constituents."""
        return await self._request("historical-sp500-constituent")  # type: ignore[attr-defined]

    async def historical_nasdaq_constituent(self) -> JSONArray:
        """Get historical Nasdaq constituents."""
        return await self._request("historical-nasdaq-constituent")  # type: ignore[attr-defined]

    async def historical_dowjones_constituent(self) -> JSONArray:
        """Get historical Dow Jones constituents."""
        return await self._request("historical-dowjones-constituent")  # type: ignore[attr-defined]
