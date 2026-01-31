"""Base client with shared logic for auth, URL building, and request execution."""

from typing import Any

import httpx

from fmp_py_client._exceptions import (
    FMPAPIError,
    FMPAuthenticationError,
    FMPConnectionError,
    FMPNotFoundError,
    FMPRateLimitError,
    FMPTimeoutError,
)

BASE_URL = "https://financialmodelingprep.com"
API_PREFIX = "/stable"


class BaseClient:
    """Shared logic for async and sync clients."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _build_url(self, path: str) -> str:
        return f"{self._base_url}{API_PREFIX}/{path.lstrip('/')}"

    def _prepare_params(self, params: dict[str, Any]) -> dict[str, Any]:
        cleaned = {k: v for k, v in params.items() if v is not None}
        cleaned["apikey"] = self._api_key
        return cleaned


class AsyncBaseClient(BaseClient):
    """Async base client with httpx.AsyncClient lifecycle."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        self._client = httpx_client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
        )
        self._owns_client = httpx_client is None

    async def __aenter__(self) -> "AsyncBaseClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = self._build_url(path)
        prepared = self._prepare_params(params or {})
        try:
            response = await self._client.get(url, params=prepared)
        except httpx.TimeoutException as e:
            raise FMPTimeoutError(f"Request to {path} timed out") from e
        except httpx.ConnectError as e:
            raise FMPConnectionError(f"Failed to connect: {e}") from e

        if response.status_code in (401, 403):
            raise FMPAuthenticationError(
                "Invalid or missing API key",
                status_code=response.status_code,
                response_body=response.text,
            )
        if response.status_code == 429:
            retry_after_header = response.headers.get("Retry-After")
            raise FMPRateLimitError(
                "Rate limit exceeded",
                retry_after=float(retry_after_header) if retry_after_header else None,
                response_body=response.text,
            )
        if response.status_code == 404:
            raise FMPNotFoundError(
                f"Resource not found: {path}",
                status_code=404,
                response_body=response.text,
            )
        if response.status_code >= 400:
            raise FMPAPIError(
                f"API error {response.status_code}: {response.text}",
                status_code=response.status_code,
                response_body=response.text,
            )

        return response.json()
