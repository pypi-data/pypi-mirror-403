import pytest

from france_travail_api.offres.models.qualite_pro import QualitePro
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "libelle": "Faire preuve d'autonomie",
                "description": "Capacité à travailler de manière indépendante",
            },
            QualitePro(
                libelle="Faire preuve d'autonomie",
                description="Capacité à travailler de manière indépendante",
            ),
        ),
        ({}, QualitePro(libelle=None, description=None)),
        (
            {"libelle": "Faire preuve d'autonomie"},
            QualitePro(libelle="Faire preuve d'autonomie", description=None),
        ),
        (
            {"description": "Une description"},
            QualitePro(libelle=None, description="Une description"),
        ),
    ],
)
def test_from_dict_should_create_qualite_pro(data: dict, expected: QualitePro) -> None:
    expect(QualitePro.from_dict(data)).to_equal(expected)
