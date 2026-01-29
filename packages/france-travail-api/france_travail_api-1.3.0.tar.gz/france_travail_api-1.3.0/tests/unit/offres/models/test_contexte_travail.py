import pytest

from france_travail_api.offres.models.contexte_travail import ContexteTravail
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "horaires": ["35H Travail le samedi", "Travail en journée"],
                "conditionsExercice": ["Port de tenue professionnelle ou d'uniforme", "Travail en équipe"],
            },
            ContexteTravail(
                horaires=["35H Travail le samedi", "Travail en journée"],
                conditions_exercice=["Port de tenue professionnelle ou d'uniforme", "Travail en équipe"],
            ),
        ),
        ({}, ContexteTravail(horaires=None, conditions_exercice=None)),
        (
            {"horaires": ["35H/semaine"]},
            ContexteTravail(horaires=["35H/semaine"], conditions_exercice=None),
        ),
        (
            {"horaires": [], "conditionsExercice": []},
            ContexteTravail(horaires=[], conditions_exercice=[]),
        ),
        (
            {"conditionsExercice": ["Travail debout"]},
            ContexteTravail(horaires=None, conditions_exercice=["Travail debout"]),
        ),
    ],
)
def test_from_dict_should_create_contexte_travail(data: dict, expected: ContexteTravail) -> None:
    expect(ContexteTravail.from_dict(data)).to_equal(expected)
