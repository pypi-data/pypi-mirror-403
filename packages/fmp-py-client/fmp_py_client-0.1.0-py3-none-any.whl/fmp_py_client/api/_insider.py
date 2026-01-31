"""Insider and institutional trading API endpoints."""

from fmp_py_client._types import JSONArray


class InsiderMixin:
    """Insider and institutional trading endpoints."""

    async def insider_trading_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest insider trades."""
        return await self._request(  # type: ignore[attr-defined]
            "insider-trading/latest",
            params={"page": page, "limit": limit},
        )

    async def insider_trading_search(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Search insider trades."""
        return await self._request(  # type: ignore[attr-defined]
            "insider-trading/search",
            params={"page": page, "limit": limit},
        )

    async def insider_trading_reporting_name(
        self,
        *,
        name: str | None = None,
    ) -> JSONArray:
        """Get insider trades by reporting name."""
        return await self._request(  # type: ignore[attr-defined]
            "insider-trading/reporting-name",
            params={"name": name},
        )

    async def insider_trading_transaction_type(self) -> JSONArray:
        """Get insider trading transaction types."""
        return await self._request("insider-trading-transaction-type")  # type: ignore[attr-defined]

    async def insider_trading_statistics(
        self, *, symbol: str | None = None
    ) -> JSONArray:
        """Get insider trading statistics."""
        return await self._request(  # type: ignore[attr-defined]
            "insider-trading/statistics",
            params={"symbol": symbol},
        )

    async def acquisition_of_beneficial_ownership(
        self,
        *,
        symbol: str | None = None,
    ) -> JSONArray:
        """Get acquisition of beneficial ownership data."""
        return await self._request(  # type: ignore[attr-defined]
            "acquisition-of-beneficial-ownership",
            params={"symbol": symbol},
        )

    async def institutional_ownership_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest institutional ownership."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/latest",
            params={"page": page, "limit": limit},
        )

    async def institutional_ownership_extract(
        self,
        *,
        cik: int | None = None,
        year: int | None = None,
        quarter: int | None = None,
    ) -> JSONArray:
        """Get institutional ownership extract."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/extract",
            params={"cik": cik, "year": year, "quarter": quarter},
        )

    async def institutional_ownership_dates(
        self,
        *,
        cik: int | None = None,
    ) -> JSONArray:
        """Get institutional ownership data dates."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/dates",
            params={"cik": cik},
        )

    async def institutional_ownership_holder_analytics(
        self,
        *,
        symbol: str | None = None,
        year: int | None = None,
        quarter: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get institutional holder analytics."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/extract-analytics/holder",
            params={
                "symbol": symbol,
                "year": year,
                "quarter": quarter,
                "page": page,
                "limit": limit,
            },
        )

    async def institutional_ownership_holder_performance_summary(
        self,
        *,
        cik: int | None = None,
        page: int | None = None,
    ) -> JSONArray:
        """Get institutional holder performance summary."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/holder-performance-summary",
            params={"cik": cik, "page": page},
        )

    async def institutional_ownership_holder_industry_breakdown(
        self,
        *,
        cik: int | None = None,
        year: int | None = None,
        quarter: int | None = None,
    ) -> JSONArray:
        """Get institutional holder industry breakdown."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/holder-industry-breakdown",
            params={"cik": cik, "year": year, "quarter": quarter},
        )

    async def institutional_ownership_symbol_positions_summary(
        self,
        *,
        symbol: str | None = None,
        year: int | None = None,
        quarter: int | None = None,
    ) -> JSONArray:
        """Get institutional symbol positions summary."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/symbol-positions-summary",
            params={"symbol": symbol, "year": year, "quarter": quarter},
        )

    async def institutional_ownership_industry_summary(
        self,
        *,
        year: int | None = None,
        quarter: int | None = None,
    ) -> JSONArray:
        """Get institutional ownership industry summary."""
        return await self._request(  # type: ignore[attr-defined]
            "institutional-ownership/industry-summary",
            params={"year": year, "quarter": quarter},
        )
