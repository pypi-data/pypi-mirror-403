import pytest

from france_travail_api.offres.models.agence import Agence
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "telephone": "06 12 34 56 78",
                "courriel": "Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX",
            },
            Agence(
                telephone="06 12 34 56 78",
                courriel="Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX",
            ),
        ),
        ({}, Agence(telephone=None, courriel=None)),
        ({"telephone": "06 12 34 56 78"}, Agence(telephone="06 12 34 56 78", courriel=None)),
        (
            {"courriel": "test@example.com"},
            Agence(telephone=None, courriel="test@example.com"),
        ),
    ],
)
def test_from_dict_should_create_agence(data: dict, expected: Agence) -> None:
    expect(Agence.from_dict(data)).to_equal(expected)
