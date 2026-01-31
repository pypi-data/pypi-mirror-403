"""Government trading API endpoints."""

from fmp_py_client._types import JSONArray


class GovernmentMixin:
    """Government trading (Senate/House) endpoints."""

    async def senate_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest Senate trading activity."""
        return await self._request(  # type: ignore[attr-defined]
            "senate-latest",
            params={"page": page, "limit": limit},
        )

    async def house_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest House trading activity."""
        return await self._request(  # type: ignore[attr-defined]
            "house-latest",
            params={"page": page, "limit": limit},
        )

    async def senate_trades(self, *, symbol: str | None = None) -> JSONArray:
        """Get Senate trades for a symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "senate-trades",
            params={"symbol": symbol},
        )

    async def senate_trades_by_name(self, *, name: str | None = None) -> JSONArray:
        """Get Senate trades by official name."""
        return await self._request(  # type: ignore[attr-defined]
            "senate-trades-by-name",
            params={"name": name},
        )

    async def house_trades(self, *, symbol: str | None = None) -> JSONArray:
        """Get House trades for a symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "house-trades",
            params={"symbol": symbol},
        )

    async def house_trades_by_name(self, *, name: str | None = None) -> JSONArray:
        """Get House trades by official name."""
        return await self._request(  # type: ignore[attr-defined]
            "house-trades-by-name",
            params={"name": name},
        )
