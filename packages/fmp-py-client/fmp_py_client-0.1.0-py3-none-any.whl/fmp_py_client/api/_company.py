"""Company profile and data API endpoints."""

from fmp_py_client._types import JSONArray


class CompanyMixin:
    """Company profile and data endpoints."""

    async def profile(self, *, symbol: str | None = None) -> JSONArray:
        """Get company profile data."""
        return await self._request(  # type: ignore[attr-defined]
            "profile",
            params={"symbol": symbol},
        )

    async def profile_cik(self, *, cik: int | None = None) -> JSONArray:
        """Get company profile by CIK number."""
        return await self._request(  # type: ignore[attr-defined]
            "profile-cik",
            params={"cik": cik},
        )

    async def company_notes(self, *, symbol: str | None = None) -> JSONArray:
        """Get company notes."""
        return await self._request(  # type: ignore[attr-defined]
            "company-notes",
            params={"symbol": symbol},
        )

    async def stock_peers(self, *, symbol: str | None = None) -> JSONArray:
        """Get stock peer comparison."""
        return await self._request(  # type: ignore[attr-defined]
            "stock-peers",
            params={"symbol": symbol},
        )

    async def company_screener(
        self,
        *,
        market_cap_more_than: float | None = None,
        market_cap_less_than: float | None = None,
        price_more_than: float | None = None,
        price_less_than: float | None = None,
        beta_more_than: float | None = None,
        beta_less_than: float | None = None,
        volume_more_than: int | None = None,
        volume_less_than: int | None = None,
        dividend_more_than: float | None = None,
        dividend_less_than: float | None = None,
        sector: str | None = None,
        industry: str | None = None,
        exchange: str | None = None,
        country: str | None = None,
        is_etf: bool | None = None,
        is_fund: bool | None = None,
        is_actively_trading: bool | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Screen companies by various criteria."""
        return await self._request(  # type: ignore[attr-defined]
            "company-screener",
            params={
                "marketCapMoreThan": market_cap_more_than,
                "marketCapLessThan": market_cap_less_than,
                "priceMoreThan": price_more_than,
                "priceLessThan": price_less_than,
                "betaMoreThan": beta_more_than,
                "betaLessThan": beta_less_than,
                "volumeMoreThan": volume_more_than,
                "volumeLessThan": volume_less_than,
                "dividendMoreThan": dividend_more_than,
                "dividendLessThan": dividend_less_than,
                "sector": sector,
                "industry": industry,
                "exchange": exchange,
                "country": country,
                "isEtf": is_etf,
                "isFund": is_fund,
                "isActivelyTrading": is_actively_trading,
                "limit": limit,
            },
        )

    async def key_executives(self, *, symbol: str | None = None) -> JSONArray:
        """Get key executives for a company."""
        return await self._request(  # type: ignore[attr-defined]
            "key-executives",
            params={"symbol": symbol},
        )

    async def executive_compensation(self, *, symbol: str | None = None) -> JSONArray:
        """Get executive compensation data."""
        return await self._request(  # type: ignore[attr-defined]
            "governance-executive-compensation",
            params={"symbol": symbol},
        )

    async def employee_count(self, *, symbol: str | None = None) -> JSONArray:
        """Get employee count for a company."""
        return await self._request(  # type: ignore[attr-defined]
            "employee-count",
            params={"symbol": symbol},
        )

    async def historical_employee_count(
        self, *, symbol: str | None = None
    ) -> JSONArray:
        """Get historical employee count."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-employee-count",
            params={"symbol": symbol},
        )

    async def market_capitalization(self, *, symbol: str | None = None) -> JSONArray:
        """Get current market capitalization."""
        return await self._request(  # type: ignore[attr-defined]
            "market-capitalization",
            params={"symbol": symbol},
        )

    async def market_capitalization_batch(
        self, *, symbols: str | None = None
    ) -> JSONArray:
        """Get market capitalization for multiple symbols (comma-separated)."""
        return await self._request(  # type: ignore[attr-defined]
            "market-capitalization-batch",
            params={"symbols": symbols},
        )

    async def historical_market_capitalization(
        self, *, symbol: str | None = None
    ) -> JSONArray:
        """Get historical market capitalization."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-market-capitalization",
            params={"symbol": symbol},
        )

    async def shares_float(self, *, symbol: str | None = None) -> JSONArray:
        """Get shares float data."""
        return await self._request(  # type: ignore[attr-defined]
            "shares-float",
            params={"symbol": symbol},
        )

    async def shares_float_all(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get all shares float data."""
        return await self._request(  # type: ignore[attr-defined]
            "shares-float-all",
            params={"page": page, "limit": limit},
        )

    async def executive_compensation_benchmark(self) -> JSONArray:
        """Get executive compensation benchmark."""
        return await self._request("executive-compensation-benchmark")  # type: ignore[attr-defined]
