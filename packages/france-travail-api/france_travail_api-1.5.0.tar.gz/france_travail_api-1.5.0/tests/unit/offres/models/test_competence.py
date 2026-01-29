import pytest

from france_travail_api.offres.models.competence import Competence
from france_travail_api.offres.models.exigence import Exigence
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "code": "483320",
                "libelle": "Faire preuve d'autonomie",
                "exigence": "E",
            },
            Competence(
                code="483320",
                libelle="Faire preuve d'autonomie",
                exigence=Exigence.OBLIGATOIRE,
            ),
        ),
        ({}, Competence(code=None, libelle=None, exigence=None)),
        (
            {
                "code": "123456",
                "libelle": "Savoir communiquer",
                "exigence": "S",
            },
            Competence(
                code="123456",
                libelle="Savoir communiquer",
                exigence=Exigence.SOUHAITE,
            ),
        ),
        (
            {
                "code": "123456",
                "libelle": "Savoir communiquer",
                "exigence": 123,  # Not a string
            },
            Competence(
                code="123456",
                libelle="Savoir communiquer",
                exigence=None,
            ),
        ),
        (
            {
                "code": "123456",
                "libelle": "Savoir communiquer",
            },
            Competence(
                code="123456",
                libelle="Savoir communiquer",
                exigence=None,
            ),
        ),
    ],
)
def test_from_dict_should_create_competence(data: dict, expected: Competence) -> None:
    expect(Competence.from_dict(data)).to_equal(expected)
