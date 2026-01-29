import pytest

from france_travail_api.auth.scope import Scope
from france_travail_api.offres.models import Offre
from tests.dsl import scenario


@pytest.mark.integration
def test_should_search_job_offers() -> None:
    flow = scenario().integration().with_live_credentials(scopes=[Scope.OFFRES]).with_offres_client()

    flow.when_searching_offres(mots_cles="developpeur", range_param="0-2").then_all_offers_are(Offre)

    flow.close()
