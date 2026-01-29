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
        """
        return HTTPResponse(
            request_id=uuid.UUID(response.request.headers["X-Request-Id"]),
            status_code=http.HTTPStatus(response.status_code),
            body=response.json(),
            headers=dict(response.headers),
        )
