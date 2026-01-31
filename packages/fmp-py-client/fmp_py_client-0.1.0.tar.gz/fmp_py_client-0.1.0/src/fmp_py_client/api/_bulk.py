"""Bulk data API endpoints."""

from fmp_py_client._types import JSONArray


class BulkMixin:
    """Bulk data download endpoints."""

    async def profile_bulk(
        self,
        *,
        part: int | None = None,
    ) -> JSONArray:
        """Get bulk company profiles."""
        return await self._request(  # type: ignore[attr-defined]
            "profile-bulk",
            params={"part": part},
        )

    async def rating_bulk(self) -> JSONArray:
        """Get bulk ratings."""
        return await self._request("rating-bulk")  # type: ignore[attr-defined]

    async def dcf_bulk(self) -> JSONArray:
        """Get bulk DCF valuations."""
        return await self._request("dcf-bulk")  # type: ignore[attr-defined]

    async def scores_bulk(self) -> JSONArray:
        """Get bulk financial scores."""
        return await self._request("scores-bulk")  # type: ignore[attr-defined]

    async def price_target_summary_bulk(self) -> JSONArray:
        """Get bulk price target summaries."""
        return await self._request("price-target-summary-bulk")  # type: ignore[attr-defined]

    async def etf_holder_bulk(
        self,
        *,
        part: int | None = None,
    ) -> JSONArray:
        """Get bulk ETF holder data."""
        return await self._request(  # type: ignore[attr-defined]
            "etf-holder-bulk",
            params={"part": part},
        )

    async def upgrades_downgrades_consensus_bulk(self) -> JSONArray:
        """Get bulk upgrades/downgrades consensus."""
        return await self._request("upgrades-downgrades-consensus-bulk")  # type: ignore[attr-defined]

    async def key_metrics_ttm_bulk(self) -> JSONArray:
        """Get bulk TTM key metrics."""
        return await self._request("key-metrics-ttm-bulk")  # type: ignore[attr-defined]

    async def ratios_ttm_bulk(self) -> JSONArray:
        """Get bulk TTM ratios."""
        return await self._request("ratios-ttm-bulk")  # type: ignore[attr-defined]

    async def peers_bulk(self) -> JSONArray:
        """Get bulk peer comparisons."""
        return await self._request("peers-bulk")  # type: ignore[attr-defined]

    async def earnings_surprises_bulk(
        self,
        *,
        year: int | None = None,
    ) -> JSONArray:
        """Get bulk earnings surprises."""
        return await self._request(  # type: ignore[attr-defined]
            "earnings-surprises-bulk",
            params={"year": year},
        )

    async def eod_bulk(self, *, date: str | None = None) -> JSONArray:
        """Get bulk end-of-day data for a specific date (YYYY-MM-DD)."""
        return await self._request(  # type: ignore[attr-defined]
            "eod-bulk",
            params={"date": date},
        )
