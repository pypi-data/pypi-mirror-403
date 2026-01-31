"""Crowdfunding and fundraising API endpoints."""

from fmp_py_client._types import JSONArray


class CrowdfundingMixin:
    """Crowdfunding and fundraising endpoints."""

    async def crowdfunding_offerings_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest crowdfunding offerings."""
        return await self._request(  # type: ignore[attr-defined]
            "crowdfunding-offerings-latest",
            params={"page": page, "limit": limit},
        )

    async def crowdfunding_offerings_search(
        self,
        *,
        name: str | None = None,
    ) -> JSONArray:
        """Search crowdfunding offerings."""
        return await self._request(  # type: ignore[attr-defined]
            "crowdfunding-offerings-search",
            params={"name": name},
        )

    async def crowdfunding_offerings(
        self,
        *,
        cik: int | None = None,
    ) -> JSONArray:
        """Get crowdfunding offerings."""
        return await self._request(  # type: ignore[attr-defined]
            "crowdfunding-offerings",
            params={"cik": cik},
        )

    async def fundraising_latest(
        self,
        *,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get latest fundraising data."""
        return await self._request(  # type: ignore[attr-defined]
            "fundraising-latest",
            params={"page": page, "limit": limit},
        )

    async def fundraising_search(self, *, name: str | None = None) -> JSONArray:
        """Search fundraising data."""
        return await self._request(  # type: ignore[attr-defined]
            "fundraising-search",
            params={"name": name},
        )

    async def fundraising(
        self,
        *,
        cik: int | None = None,
    ) -> JSONArray:
        """Get fundraising data."""
        return await self._request(  # type: ignore[attr-defined]
            "fundraising",
            params={"cik": cik},
        )

    async def ipos_prospectus(self) -> JSONArray:
        """Get IPO prospectus data."""
        return await self._request("ipos-prospectus")  # type: ignore[attr-defined]
