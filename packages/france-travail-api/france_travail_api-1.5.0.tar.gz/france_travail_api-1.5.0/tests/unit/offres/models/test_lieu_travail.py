import pytest

from france_travail_api.offres.models.lieu_travail import LieuTravail
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "libelle": "74 - ANNECY",
                "latitude": 45.901584,
                "longitude": 6.125296,
                "codePostal": "74000",
                "commune": "74010",
            },
            LieuTravail(
                libelle="74 - ANNECY",
                latitude=45.901584,
                longitude=6.125296,
                code_postal="74000",
                commune="74010",
            ),
        ),
        (
            {},
            LieuTravail(
                libelle=None,
                latitude=None,
                longitude=None,
                code_postal=None,
                commune=None,
            ),
        ),
        (
            {
                "libelle": "74 - ANNECY",
                "codePostal": "74000",
            },
            LieuTravail(
                libelle="74 - ANNECY",
                latitude=None,
                longitude=None,
                code_postal="74000",
                commune=None,
            ),
        ),
    ],
)
def test_from_dict_should_create_lieu_travail(data: dict, expected: LieuTravail) -> None:
    expect(LieuTravail.from_dict(data)).to_equal(expected)
