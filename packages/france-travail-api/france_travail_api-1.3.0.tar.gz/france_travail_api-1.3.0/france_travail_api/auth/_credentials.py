import datetime
import threading
from typing import Sequence

from france_travail_api.auth._token import Token
from france_travail_api.auth.scope import Scope, Scopes
from france_travail_api.exceptions import FranceTravailException
from france_travail_api.http_transport._http_client import HttpClient

_OAUTH2_ACCESS_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"


class FranceTravailCredentials:
    """
    Handles the OAuth2 Client Credentials Grant flow to interact with the France Travail API.

    Parameters
    ----------
    client_id : str
        Application identifier provided by France Travail.
    client_secret : str
        Application secret key provided by France Travail.
    scopes : Sequence[Scope]
        List of API scopes defining accessible resources.
        See `france_travail_api.Scope` for available scopes.
    http_client : HttpClient
        Internal HTTP client for making requests. Not intended for direct use.
    """

    def __init__(self, client_id: str, client_secret: str, scopes: Sequence[Scope], http_client: HttpClient) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = Scopes(scopes)
        self._http_client = http_client

        self._token: Token | None = None
        self._lock = threading.Lock()

    def get_token(self, now: datetime.datetime = datetime.datetime.now(datetime.UTC)) -> Token:
        """
        Get an OAuth2 access token.

        Parameters
        ----------
        now : datetime.datetime
            Current datetime, defaults to the current time.

        Returns
        -------
        Token
            OAuth2 access token.
        """
        with self._lock:
            if self._has_valid_token(now):
                return self._token  # type: ignore[return-value]

        with self._lock:
            if self._has_valid_token(now):  # pragma: no cover
                return self._token  # type: ignore[return-value]

            response = self._http_client.post(
                url=_OAUTH2_ACCESS_TOKEN_URL,
                payload={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scopes,
                },
            )
            if not response.status_code.is_success:
                raise FranceTravailException.from_http_response(response)

            self._token = Token.from_response(response, now)
            return self._token

    def to_authorization_header(self) -> dict[str, str]:
        """
        Convert the token to an Authorization header.

        Returns
        -------
        dict[str, str]
            Authorization header with the token value.
        """
        return self.get_token().to_authorization_header()

    def _has_valid_token(self, now: datetime.datetime) -> bool:
        return self._token is not None and not self._token.is_expired(now)
