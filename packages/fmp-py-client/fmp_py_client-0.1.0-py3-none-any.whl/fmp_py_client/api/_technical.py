"""Technical indicators API endpoints."""

from fmp_py_client._types import JSONArray, Timeframe


class TechnicalMixin:
    """Technical indicators endpoints."""

    async def sma(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Simple Moving Average (SMA)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/sma",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def ema(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Exponential Moving Average (EMA)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/ema",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def wma(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Weighted Moving Average (WMA)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/wma",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def dema(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Double Exponential Moving Average (DEMA)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/dema",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def tema(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Triple Exponential Moving Average (TEMA)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/tema",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def rsi(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Relative Strength Index (RSI)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/rsi",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def standard_deviation(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Standard Deviation."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/standarddeviation",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def williams(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Williams %R."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/williams",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )

    async def adx(
        self,
        *,
        symbol: str | None = None,
        period_length: int | None = None,
        timeframe: Timeframe | None = None,
    ) -> JSONArray:
        """Get Average Directional Index (ADX)."""
        return await self._request(  # type: ignore[attr-defined]
            "technical-indicators/adx",
            params={
                "symbol": symbol,
                "periodLength": period_length,
                "timeframe": timeframe,
            },
        )
