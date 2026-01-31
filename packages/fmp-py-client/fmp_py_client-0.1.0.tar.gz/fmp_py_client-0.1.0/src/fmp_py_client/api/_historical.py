"""Historical price API endpoints."""

from fmp_py_client._types import JSONArray


class HistoricalMixin:
    """Historical price data endpoints."""

    async def historical_price_eod_light(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get light historical end-of-day prices."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-price-eod/light",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_price_eod_full(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get full historical end-of-day prices."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-price-eod/full",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_price_eod_non_split_adjusted(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get non-split-adjusted historical end-of-day prices."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-price-eod/non-split-adjusted",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_price_eod_dividend_adjusted(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get dividend-adjusted historical end-of-day prices."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-price-eod/dividend-adjusted",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_1min(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 1-minute interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/1min",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_5min(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 5-minute interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/5min",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_15min(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 15-minute interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/15min",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_30min(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 30-minute interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/30min",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_1hour(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 1-hour interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/1hour",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

    async def historical_chart_4hour(
        self,
        symbol: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> JSONArray:
        """Get 4-hour interval chart data."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-chart/4hour",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )
