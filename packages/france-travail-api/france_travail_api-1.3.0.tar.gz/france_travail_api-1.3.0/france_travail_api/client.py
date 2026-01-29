from typing import Sequence

from france_travail_api.auth._credentials import FranceTravailCredentials
from france_travail_api.auth.scope import Scope
from france_travail_api.http_transport._http_client import HttpClient
from france_travail_api.offres._client import FranceTravailOffresClient


class FranceTravailClient:
    """
    Client for interacting with the France Travail API.

    The FranceTravailClient provides a high-level interface to access France Travail services.

    Parameters
    ----------
    client_id : str
        Application identifier provided by France Travail.
    client_secret : str
        Application secret key provided by France Travail.
    scopes : Sequence[Scope]
        List of API scopes defining accessible resources.
        See `france_travail_api.Scope` for available scopes.
    _http_client : HttpClient
        Internal HTTP client for making requests. Not intended for direct use.

    Attributes
    ----------
    offres : FranceTravailOffresClient
        Client for accessing job offers.

    Notes
    -----
    The client handles OAuth2 authentication automatically. Access tokens are
    obtained and refreshed as needed during API calls.

    The client should be used as a context manager to ensure proper cleanup
    of HTTP connections.

    Examples
    --------
    Initialize and manage the client lifecycle:

    >>> from france_travail_api import FranceTravailClient
    >>>
    >>> with FranceTravailClient(...) as client:
    ...     job_offers = client.offres.search(mots_cles="développeur Python")

    See Also
    --------
    Scope : Available API scopes
    FranceTravailOffresClient : Client for accessing job offers

    References
    ----------
    [1] France Travail API Documentation
           https://francetravail.io/data/api
    """

    def __init__(
        self, client_id: str, client_secret: str, scopes: Sequence[Scope], _http_client: HttpClient | None = None
    ) -> None:
        self._http_client = _http_client or HttpClient()
        self._credentials = FranceTravailCredentials(client_id, client_secret, scopes, self._http_client)

        self.offres = FranceTravailOffresClient(self._credentials, self._http_client)

    def close(self) -> None:
        """
        Close the client and its underlying HTTP client.
        """
        self._http_client.close()

    async def close_async(self) -> None:
        """
        Close the client and its underlying HTTP client asynchronously.
        """
        await self._http_client.close_async()

    def __enter__(self) -> "FranceTravailClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    async def __aenter__(self) -> "FranceTravailClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close_async()
