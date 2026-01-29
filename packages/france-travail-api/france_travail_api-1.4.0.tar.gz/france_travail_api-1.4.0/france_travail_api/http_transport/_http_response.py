import http
import uuid
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class HTTPResponse:
    """
    Represents an HTTP response from the server.

    Parameters
    ----------
    status_code : http.HTTPStatus
        HTTP status code.
    body : dict[str, Any]
        Response body.
    request_id : uuid.UUID
        Request ID for the request.
    headers : dict[str, str]
        Response headers.
    """

    status_code: http.HTTPStatus
    body: dict[str, Any]
    request_id: uuid.UUID
    headers: dict[str, str]

    @staticmethod
    def from_httpx_response(response: httpx.Response) -> "HTTPResponse":
        """
        Create an HTTPResponse from an HTTPX response.

        Parameters
        ----------
        response : httpx.Response

        Returns
        -------
        HTTPResponse

        Notes
        -----
        When the API returns HTTP 204 No Content (e.g., when a job offer is not found),
        the response has no body. In such cases, an empty dictionary is returned to maintain
        type consistency and prevent JSON parsing errors.
        """
        return HTTPResponse(
            request_id=uuid.UUID(response.request.headers["X-Request-Id"]),
            status_code=http.HTTPStatus(response.status_code),
            body=response.json() if response.text else {},  # Empty dict for HTTP 204 No Content
            headers=dict(response.headers),
        )
