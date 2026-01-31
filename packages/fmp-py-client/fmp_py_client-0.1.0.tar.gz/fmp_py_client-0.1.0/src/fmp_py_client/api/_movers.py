"""Market movers API endpoints."""

from fmp_py_client._types import JSONArray


class MoversMixin:
    """Market movers endpoints (gainers, losers, most active)."""

    async def biggest_gainers(self) -> JSONArray:
        """Get biggest gaining stocks."""
        return await self._request("biggest-gainers")  # type: ignore[attr-defined]

    async def biggest_losers(self) -> JSONArray:
        """Get biggest losing stocks."""
        return await self._request("biggest-losers")  # type: ignore[attr-defined]

    async def most_actives(self) -> JSONArray:
        """Get most actively traded stocks."""
        return await self._request("most-actives")  # type: ignore[attr-defined]
