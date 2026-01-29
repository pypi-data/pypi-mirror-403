import pytest

from france_travail_api.offres.models.salaire import Salaire
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "libelle": "Mensuel de 1923.00 Euros sur 12 mois",
                "commentaire": "Selon expérience",
                "complement1": "Véhicule de fonction",
                "complement2": "Prime de vacances",
            },
            Salaire(
                libelle="Mensuel de 1923.00 Euros sur 12 mois",
                commentaire="Selon expérience",
                complement1="Véhicule de fonction",
                complement2="Prime de vacances",
                liste_complements=None,
            ),
        ),
        (
            {},
            Salaire(
                libelle=None,
                commentaire=None,
                complement1=None,
                complement2=None,
                liste_complements=None,
            ),
        ),
        (
            {"libelle": "Annuel de 38000.0 Euros à 45000.0 Euros sur 12.0 mois"},
            Salaire(
                libelle="Annuel de 38000.0 Euros à 45000.0 Euros sur 12.0 mois",
                commentaire=None,
                complement1=None,
                complement2=None,
                liste_complements=None,
            ),
        ),
    ],
)
def test_from_dict_should_create_salaire(data: dict, expected: Salaire) -> None:
    expect(Salaire.from_dict(data)).to_equal(expected)
