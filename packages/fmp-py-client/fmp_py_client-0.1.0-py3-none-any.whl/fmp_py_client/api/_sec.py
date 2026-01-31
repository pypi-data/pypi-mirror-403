"""SEC filings API endpoints."""

from fmp_py_client._types import JSONArray


class SECMixin:
    """SEC filings and classification endpoints."""

    async def sec_filings_8k(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get SEC 8-K filings."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-8k",
            params={"from": from_date, "to": to_date, "page": page, "limit": limit},
        )

    async def sec_filings_financials(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Get SEC financial filings."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-financials",
            params={"from": from_date, "to": to_date, "page": page, "limit": limit},
        )

    async def sec_filings_search_form_type(
        self,
        *,
        form_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Search SEC filings by form type."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-search/form-type",
            params={
                "formType": form_type,
                "from": from_date,
                "to": to_date,
                "page": page,
                "limit": limit,
            },
        )

    async def sec_filings_search_symbol(
        self,
        *,
        symbol: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Search SEC filings by symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-search/symbol",
            params={
                "symbol": symbol,
                "from": from_date,
                "to": to_date,
                "page": page,
                "limit": limit,
            },
        )

    async def sec_filings_search_cik(
        self,
        *,
        cik: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> JSONArray:
        """Search SEC filings by CIK."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-search/cik",
            params={
                "cik": cik,
                "from": from_date,
                "to": to_date,
                "page": page,
                "limit": limit,
            },
        )

    async def sec_filings_company_search_name(
        self, *, company: str | None = None
    ) -> JSONArray:
        """Search SEC companies by name."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-company-search/name",
            params={"company": company},
        )

    async def sec_filings_company_search_symbol(
        self, *, symbol: str | None = None
    ) -> JSONArray:
        """Search SEC companies by symbol."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-company-search/symbol",
            params={"symbol": symbol},
        )

    async def sec_filings_company_search_cik(
        self, *, cik: int | None = None
    ) -> JSONArray:
        """Search SEC companies by CIK."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-filings-company-search/cik",
            params={"cik": cik},
        )

    async def sec_profile(
        self,
        *,
        symbol: str | None = None,
    ) -> JSONArray:
        """Get SEC profile."""
        return await self._request(  # type: ignore[attr-defined]
            "sec-profile",
            params={"symbol": symbol},
        )

    async def standard_industrial_classification_list(self) -> JSONArray:
        """Get SIC codes list."""
        return await self._request("standard-industrial-classification-list")  # type: ignore[attr-defined]

    async def industry_classification_search(self) -> JSONArray:
        """Search industry classifications."""
        return await self._request("industry-classification-search")  # type: ignore[attr-defined]

    async def all_industry_classification(self) -> JSONArray:
        """Get all industry classifications."""
        return await self._request("all-industry-classification")  # type: ignore[attr-defined]
