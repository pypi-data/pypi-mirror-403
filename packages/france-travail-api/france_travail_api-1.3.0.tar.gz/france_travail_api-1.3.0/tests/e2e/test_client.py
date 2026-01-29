import pytest

from france_travail_api.offres.models.offre import Offre
from tests.dsl import scenario


@pytest.mark.e2e
def test_should_find_job_offers() -> None:
    flow = scenario().e2e()

    flow.when_searching_offres_e2e(mots_cles="developpeur", range_param="0-2").then_all_offers_are(Offre)

    flow.close()
