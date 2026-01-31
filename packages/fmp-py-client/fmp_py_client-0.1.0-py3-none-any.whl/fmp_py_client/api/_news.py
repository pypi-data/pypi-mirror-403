"""News and analyst data API endpoints."""

from fmp_py_client._types import JSONArray


class NewsMixin:
    """News and analyst data endpoints."""

    async def fmp_articles(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get FMP articles."""
        return await self._request(  # type: ignore[attr-defined]
            "fmp-articles",
            params={"page": page, "limit": limit},
        )

    async def news_general_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest general news."""
        return await self._request(  # type: ignore[attr-defined]
            "news/general-latest",
            params={"page": page, "limit": limit},
        )

    async def news_press_releases_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest press releases."""
        return await self._request(  # type: ignore[attr-defined]
            "news/press-releases-latest",
            params={"page": page, "limit": limit},
        )

    async def news_stock_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest stock news."""
        return await self._request(  # type: ignore[attr-defined]
            "news/stock-latest",
            params={"page": page, "limit": limit},
        )

    async def news_crypto_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest crypto news."""
        return await self._request(  # type: ignore[attr-defined]
            "news/crypto-latest",
            params={"page": page, "limit": limit},
        )

    async def news_forex_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest forex news."""
        return await self._request(  # type: ignore[attr-defined]
            "news/forex-latest",
            params={"page": page, "limit": limit},
        )

    async def news_press_releases(
        self,
        *,
        symbols: str | None = None,
    ) -> JSONArray:
        """Get press releases for a symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "news/press-releases",
            params={"symbols": symbols},
        )

    async def news_stock(
        self,
        *,
        symbols: str | None = None,
    ) -> JSONArray:
        """Get stock news for a symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "news/stock",
            params={"symbols": symbols},
        )

    async def news_crypto(
        self,
        *,
        symbols: str | None = None,
    ) -> JSONArray:
        """Get crypto news for a symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "news/crypto",
            params={"symbols": symbols},
        )

    async def news_forex(
        self,
        *,
        symbols: str | None = None,
    ) -> JSONArray:
        """Get forex news for a pair."""
        return await self._request(  # type: ignore[attr-defined]
            "news/forex",
            params={"symbols": symbols},
        )

    async def analyst_estimates(
        self,
        *,
        symbol: str | None = None,
        period: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get analyst estimates."""
        return await self._request(  # type: ignore[attr-defined]
            "analyst-estimates",
            params={"symbol": symbol, "period": period, "page": page, "limit": limit},
        )

    async def ratings_snapshot(self, *, symbol: str | None = None) -> JSONArray:
        """Get ratings snapshot."""
        return await self._request(  # type: ignore[attr-defined]
            "ratings-snapshot",
            params={"symbol": symbol},
        )

    async def ratings_historical(self, *, symbol: str | None = None) -> JSONArray:
        """Get historical ratings."""
        return await self._request(  # type: ignore[attr-defined]
            "ratings-historical",
            params={"symbol": symbol},
        )

    async def price_target_summary(self, *, symbol: str | None = None) -> JSONArray:
        """Get price target summary."""
        return await self._request(  # type: ignore[attr-defined]
            "price-target-summary",
            params={"symbol": symbol},
        )

    async def price_target_consensus(self, *, symbol: str | None = None) -> JSONArray:
        """Get price target consensus."""
        return await self._request(  # type: ignore[attr-defined]
            "price-target-consensus",
            params={"symbol": symbol},
        )

    async def grades(self, *, symbol: str | None = None) -> JSONArray:
        """Get analyst grades."""
        return await self._request(  # type: ignore[attr-defined]
            "grades",
            params={"symbol": symbol},
        )

    async def grades_historical(self, *, symbol: str | None = None) -> JSONArray:
        """Get historical analyst grades."""
        return await self._request(  # type: ignore[attr-defined]
            "grades-historical",
            params={"symbol": symbol},
        )

    async def grades_consensus(self, *, symbol: str | None = None) -> JSONArray:
        """Get analyst grades consensus."""
        return await self._request(  # type: ignore[attr-defined]
            "grades-consensus",
            params={"symbol": symbol},
        )
