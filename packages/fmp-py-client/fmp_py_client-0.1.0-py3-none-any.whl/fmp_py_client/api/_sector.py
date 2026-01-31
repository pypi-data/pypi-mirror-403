"""Sector and industry performance API endpoints."""

from fmp_py_client._types import JSONArray


class SectorMixin:
    """Sector and industry performance endpoints."""

    async def sector_performance_snapshot(
        self,
        *,
        date: str | None = None,
    ) -> JSONArray:
        """Get sector performance snapshot."""
        return await self._request(  # type: ignore[attr-defined]
            "sector-performance-snapshot",
            params={"date": date},
        )

    async def industry_performance_snapshot(
        self,
        *,
        date: str | None = None,
    ) -> JSONArray:
        """Get industry performance snapshot."""
        return await self._request(  # type: ignore[attr-defined]
            "industry-performance-snapshot",
            params={"date": date},
        )

    async def historical_sector_performance(
        self,
        *,
        sector: str | None = None,
    ) -> JSONArray:
        """Get historical sector performance."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-sector-performance",
            params={"sector": sector},
        )

    async def historical_industry_performance(
        self,
        *,
        industry: str | None = None,
    ) -> JSONArray:
        """Get historical industry performance."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-industry-performance",
            params={"industry": industry},
        )

    async def sector_pe_snapshot(
        self,
        *,
        date: str | None = None,
    ) -> JSONArray:
        """Get sector P/E ratio snapshot."""
        return await self._request(  # type: ignore[attr-defined]
            "sector-pe-snapshot",
            params={"date": date},
        )

    async def industry_pe_snapshot(
        self,
        *,
        date: str | None = None,
    ) -> JSONArray:
        """Get industry P/E ratio snapshot."""
        return await self._request(  # type: ignore[attr-defined]
            "industry-pe-snapshot",
            params={"date": date},
        )

    async def historical_sector_pe(
        self,
        *,
        sector: str | None = None,
    ) -> JSONArray:
        """Get historical sector P/E ratios."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-sector-pe",
            params={"sector": sector},
        )

    async def historical_industry_pe(
        self,
        *,
        industry: str | None = None,
    ) -> JSONArray:
        """Get historical industry P/E ratios."""
        return await self._request(  # type: ignore[attr-defined]
            "historical-industry-pe",
            params={"industry": industry},
        )
