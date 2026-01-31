"""Economics and market timing API endpoints."""

from fmp_py_client._types import JSONArray


class EconomicsMixin:
    """Economics and market data endpoints."""

    async def treasury_rates(self) -> JSONArray:
        """Get US treasury rates."""
        return await self._request("treasury-rates")  # type: ignore[attr-defined]

    async def economic_indicators(self, *, name: str | None = None) -> JSONArray:
        """Get economic indicators by name (e.g., GDP, CPI)."""
        return await self._request(  # type: ignore[attr-defined]
            "economic-indicators",
            params={"name": name},
        )

    async def economic_calendar(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get economic data releases calendar."""
        return await self._request(  # type: ignore[attr-defined]
            "economic-calendar",
            params={"from": from_date, "to": to_date},
        )

    async def market_risk_premium(self) -> JSONArray:
        """Get market risk premium by country."""
        return await self._request("market-risk-premium")  # type: ignore[attr-defined]

    async def commodities_list(self) -> JSONArray:
        """Get list of available commodities."""
        return await self._request("commodities-list")  # type: ignore[attr-defined]

    async def forex_list(self) -> JSONArray:
        """Get list of available forex pairs."""
        return await self._request("forex-list")  # type: ignore[attr-defined]

    async def cryptocurrency_list(self) -> JSONArray:
        """Get list of available cryptocurrencies."""
        return await self._request("cryptocurrency-list")  # type: ignore[attr-defined]

    async def exchange_market_hours(self, *, exchange: str | None = None) -> JSONArray:
        """Get market hours for an exchange."""
        return await self._request(  # type: ignore[attr-defined]
            "exchange-market-hours",
            params={"exchange": exchange},
        )

    async def all_exchange_market_hours(self) -> JSONArray:
        """Get market hours for all exchanges."""
        return await self._request("all-exchange-market-hours")  # type: ignore[attr-defined]

    async def holidays_by_exchange(self, *, exchange: str | None = None) -> JSONArray:
        """Get holidays for an exchange."""
        return await self._request(  # type: ignore[attr-defined]
            "holidays-by-exchange",
            params={"exchange": exchange},
        )
