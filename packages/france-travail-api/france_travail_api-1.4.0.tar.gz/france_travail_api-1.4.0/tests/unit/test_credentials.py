import datetime

from france_travail_api.auth._token import Token
from france_travail_api.auth.scope import Scope
from france_travail_api.exceptions import FranceTravailException
from tests.dsl import scenario


def test_should_return_token() -> None:
    flow = (
        scenario()
        .unit()
        .with_token_response()
        .with_credentials(client_id="client-id", client_secret="client-secret", scopes=[Scope.OFFRES])
    )

    flow.when_get_token().then_token_is(
        Token(
            access_token="my_token",
            expires_at=flow.now + datetime.timedelta(seconds=1_499),
            scope="api_offresdemploiv2 o2dsoffre",
            token_type="Bearer",
        )
    )


def test_should_return_cached_token_if_not_expired() -> None:
    flow = (
        scenario()
        .unit()
        .with_token_response(access_token="my_token1")
        .with_token_response(access_token="my_token2")
        .with_credentials(client_id="client-id", client_secret="client-secret", scopes=[Scope.OFFRES])
    )

    flow.when_get_token()
    flow.when_get_token().then_token_is(
        Token(
            access_token="my_token1",
            expires_at=flow.now + datetime.timedelta(seconds=1_499),
            scope="api_offresdemploiv2 o2dsoffre",
            token_type="Bearer",
        )
    )


def test_should_raise_base_exception_when_http_client_returns_error() -> None:
    scenario().unit().with_error_response().with_credentials(
        client_id="client-id", client_secret="client-secret", scopes=[Scope.OFFRES]
    ).when_get_token().then_exception_is(
        FranceTravailException,
        match="An error occurred while communicating with the France Travail API: An unknown error occurred",
    )


def test_should_return_authorization_header() -> None:
    scenario().unit().with_token_response().with_credentials(
        client_id="client-id", client_secret="client-secret", scopes=[Scope.OFFRES]
    ).when_authorization_header().then_authorization_header_is({"Authorization": "Bearer my_token"})
