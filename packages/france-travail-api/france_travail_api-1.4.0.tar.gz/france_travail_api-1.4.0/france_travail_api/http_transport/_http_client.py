import uuid
from typing import Any

import httpx

from france_travail_api.http_transport._http_response import HTTPResponse


class HttpClient:
    """
    Basic wrapper around `httpx` client to make standardized sync and async HTTP requests.

    TODO: better retry logic, logging, monitoring...

    Parameters
    ----------
    timeout : float (default: 30.0)
        Timeout for HTTP requests.

    Examples
    --------
    >>> from france_travail_api.http_transport._http_client import HttpClient
    >>> client = HttpClient()
    >>> response = client.get("https://api.example.com/endpoint")
    >>> response.status_code
    <HTTPStatus.OK: 200>
    >>> response.body
    {"key": "value"}
    >>> response.headers
    {"Content-Type": "application/json"}
    >>> client.close()
    """

    def __init__(self, timeout: float = 30.0):
        self.sync_client = httpx.Client(timeout=timeout)
        self.async_client = httpx.AsyncClient(timeout=timeout)

    def get(self, url: str, headers: dict[str, str] | None = None) -> HTTPResponse:
        """
        Make a GET request.

        Parameters
        ----------
        url : str
            URL to make the request to.
        headers : dict[str, str] | None
            Headers to include in the request.

        Returns
        -------
        HTTPResponse
            Response from the server.
        """
        return HTTPResponse.from_httpx_response(
            self.sync_client.get(url, headers=self._build_request_headers("GET", headers))
        )

    async def get_async(self, url: str, headers: dict[str, str] | None = None) -> HTTPResponse:
        """
        Make an asynchronous GET request.

        Parameters
        ----------
        url : str
            URL to make the request to.
        headers : dict[str, str] | None
            Headers to include in the request.

        Returns
        -------
        HTTPResponse
            Response from the server.
        """
        return HTTPResponse.from_httpx_response(
            await self.async_client.get(url, headers=self._build_request_headers("GET", headers))
        )

    def post(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> HTTPResponse:
        """
        Make a POST request.

        Parameters
        ----------
        url : str
            URL to make the request to.
        payload : dict[str, Any]
            Payload to include in the request.
        headers : dict[str, str] | None
            Headers to include in the request.

        Returns
        -------
        HTTPResponse
            Response from the server.
        """
        return HTTPResponse.from_httpx_response(
            self.sync_client.post(url, data=payload, headers=self._build_request_headers("POST", headers))
        )

    async def post_async(
        self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> HTTPResponse:
        """
        Make an asynchronous POST request.

        Parameters
        ----------
        url : str
            URL to make the request to.
        payload : dict[str, Any]
            Payload to include in the request.
        headers : dict[str, str] | None
            Headers to include in the request.

        Returns
        -------
        HTTPResponse
            Response from the server.
        """
        return HTTPResponse.from_httpx_response(
            await self.async_client.post(url, data=payload, headers=self._build_request_headers("POST", headers))
        )

    def close(self) -> None:
        """
        Close the HTTP client.

        This method should be called when the client is no longer needed.
        """
        self.sync_client.close()

    async def close_async(self) -> None:
        """
        Close the asynchronous HTTP client.

        This method should be called when the client is no longer needed.
        """
        await self.async_client.aclose()

    def _build_request_headers(self, verb: str, headers: dict[str, str] | None) -> dict:
        return {**(headers or {}), "X-Request-Id": str(uuid.uuid4())}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sync_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.async_client.aclose()
