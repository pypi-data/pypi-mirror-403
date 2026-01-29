import uuid

from france_travail_api.http_transport._http_response import HTTPResponse


class FranceTravailException(Exception):
    """
    Base exception for France Travail API errors.

    Parameters
    ----------
    message : str
        Error message.
    request_id : uuid.UUID | None
        Request ID for the failed request.

    Examples
    --------
    You should use the `FranceTravailException.from_http_response` method to
    raise a specific exception from an HTTP response.
    >>> from france_travail_api.exceptions import FranceTravailException
    >>> from france_travail_api.http_transport._http_response import HTTPResponse
    >>> response = HTTPResponse(...)
    >>> try:
    ...     raise FranceTravailException.from_http_response(response)
    ... except FranceTravailException as e:
    ...     print(e.message)
    ...     print(e.request_id)
    """

    def __init__(
        self,
        message: str,
        request_id: uuid.UUID | None = None,
    ) -> None:
        self.request_id = request_id
        super().__init__(message)

    @classmethod
    def from_http_response(cls, response: HTTPResponse) -> "FranceTravailException":
        """
        Create a specific exception from an HTTP response.

        Parameters
        ----------
        response : HTTPResponse
            HTTP response containing the error details.

        Returns
        -------
        FranceTravailException
            Specific exception for the given error.
            See `FranceTravailException` for available exceptions.
        """
        match response.body.get("error"):
            case "invalid_client":
                return BadCredentialsException(
                    "Your France Travail client ID or secret are invalid.",
                    request_id=response.request_id,
                )
            case _:
                error_description = response.body.get("error_description")
                return FranceTravailException(
                    f"An error occurred while communicating with the France Travail API: {error_description}",
                    request_id=response.request_id,
                )


class ClientAuthenticationException(FranceTravailException):
    pass


class BadCredentialsException(ClientAuthenticationException):
    pass
