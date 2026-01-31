"""Mergers and acquisitions API endpoints."""

from fmp_py_client._types import JSONArray


class MergersMixin:
    """Mergers and acquisitions endpoints."""

    async def mergers_acquisitions_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest M&A activity."""
        return await self._request(  # type: ignore[attr-defined]
            "mergers-acquisitions-latest",
            params={"page": page, "limit": limit},
        )

    async def mergers_acquisitions_search(
        self, *, name: str | None = None
    ) -> JSONArray:
        """Search M&A activity by company name."""
        return await self._request(  # type: ignore[attr-defined]
            "mergers-acquisitions-search",
            params={"name": name},
        )
