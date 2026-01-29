import datetime

import pytest

from france_travail_api.auth.scope import Scope
from tests.dsl import scenario


@pytest.mark.integration
def test_should_return_token() -> None:
    flow = scenario().integration().with_live_credentials(scopes=[Scope.OFFRES])

    flow.when_get_token()

    flow.then_token_has_access_token()
    flow.then_token_expires_at(flow.now + datetime.timedelta(seconds=1_499))
    flow.then_token_scope_is(Scope.OFFRES)
    flow.then_token_type_is("Bearer")

    flow.close()


@pytest.mark.integration
def test_should_raise_exception_if_client_id_or_secret_are_invalid() -> None:
    flow = (
        scenario()
        .integration()
        .with_credentials(client_id="invalid-client-id", client_secret="invalid-client-secret", scopes=[Scope.OFFRES])
    )

    flow.when_get_token().then_exception_is(Exception, match="Your France Travail client ID or secret are invalid")

    flow.close()
