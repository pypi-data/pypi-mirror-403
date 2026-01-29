import datetime
from dataclasses import dataclass

from france_travail_api.http_transport._http_response import HTTPResponse


@dataclass(frozen=True)
class Token:
    """
    Represents an OAuth2 access token from France Travail API Client Credentials Grant flow.

    Parameters
    ----------
    access_token : str
        Access token value.
    expires_at : datetime.datetime
        Expiration date of the token.
    scope : str
        Scope of the token.
    token_type : str
        Token type.
    """

    access_token: str
    expires_at: datetime.datetime
    scope: str
    token_type: str

    @staticmethod
    def from_response(response: HTTPResponse, now: datetime.datetime) -> "Token":
        """
        Create a Token from an HTTP response.

        Parameters
        ----------
        response : HTTPResponse
            HTTP response containing the token details.
        now : datetime.datetime
            Current datetime.

        Returns
        -------
        Token
        """
        body = response.body
        return Token(
            access_token=body["access_token"],
            expires_at=now + datetime.timedelta(seconds=body["expires_in"]),
            scope=body["scope"],
            token_type=body["token_type"],
        )

    def to_authorization_header(self) -> dict[str, str]:
        """
        Convert the token to an Authorization header.

        Returns
        -------
        dict[str, str]
            Authorization header with the token value.
        """
        return {"Authorization": f"Bearer {self.access_token}"}

    def is_expired(self, now: datetime.datetime) -> bool:
        """
        Check if the token is expired.
        To be used to check if the token needs to be refreshed before using the client.

        Parameters
        ----------
        now : datetime.datetime
            Current datetime.

        Returns
        -------
        bool
            True if the token is expired, False otherwise.
        """
        return now > self.expires_at - datetime.timedelta(seconds=60)
