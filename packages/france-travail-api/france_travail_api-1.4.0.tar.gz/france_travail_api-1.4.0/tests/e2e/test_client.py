import pytest

from france_travail_api.offres.models.offre import Offre
from tests.dsl import scenario
from tests.dsl.scenario import Scenario


@pytest.mark.e2e
def test_should_find_job_offers() -> None:
    flow = scenario().e2e()

    flow.when_searching_offres_e2e(mots_cles="developpeur", range_param="0-2").then_all_offers_are(Offre)

    flow.close()


@pytest.mark.e2e
def test_should_get_job_offer_by_id() -> None:
    flow = scenario().e2e()

    offer_id = _get_first_valid_offer_id(flow)

    flow.when_getting_offre_e2e(offer_id=offer_id).then_offre_should_be_instance_of(Offre)

    flow.close()


def _get_first_valid_offer_id(flow: Scenario) -> str:
    flow.when_searching_offres_e2e(mots_cles="developpeur", range_param="0-0")

    assert flow._offers is not None and len(flow._offers) > 0, "No job offers found in search"
    first_offer = flow._offers[0]
    assert first_offer.id is not None, "First offer has no ID"

    return first_offer.id
