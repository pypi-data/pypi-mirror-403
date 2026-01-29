import pytest

from france_travail_api.offres.models.exigence import Exigence
from france_travail_api.offres.models.formation import Formation
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "codeFormation": "21538",
                "domaineLibelle": "boulangerie",
                "niveauLibelle": "CAP, BEP et équivalents",
                "commentaire": "Mention bien souhaitée",
                "exigence": "E",
            },
            Formation(
                code_formation="21538",
                domaine_libelle="boulangerie",
                niveau_libelle="CAP, BEP et équivalents",
                commentaire="Mention bien souhaitée",
                exigence=Exigence.OBLIGATOIRE,
            ),
        ),
        (
            {},
            Formation(
                code_formation=None,
                domaine_libelle=None,
                niveau_libelle=None,
                commentaire=None,
                exigence=None,
            ),
        ),
        (
            {
                "codeFormation": "12345",
                "domaineLibelle": "informatique",
                "niveauLibelle": "Bac+5",
                "exigence": "S",
            },
            Formation(
                code_formation="12345",
                domaine_libelle="informatique",
                niveau_libelle="Bac+5",
                commentaire=None,
                exigence=Exigence.SOUHAITE,
            ),
        ),
        (
            {
                "codeFormation": "21538",
                "domaineLibelle": "boulangerie",
                "niveauLibelle": "CAP, BEP et équivalents",
            },
            Formation(
                code_formation="21538",
                domaine_libelle="boulangerie",
                niveau_libelle="CAP, BEP et équivalents",
                commentaire=None,
                exigence=None,
            ),
        ),
    ],
)
def test_from_dict_should_create_formation(data: dict, expected: Formation) -> None:
    expect(Formation.from_dict(data)).to_equal(expected)


@pytest.mark.parametrize("invalid_code", ["INVALID", "X", "123"])
def test_from_dict_should_raise_error_when_exigence_code_is_invalid(invalid_code: str) -> None:
    data = {
        "codeFormation": "12345",
        "domaineLibelle": "informatique",
        "exigence": invalid_code,
    }

    expect(lambda: Formation.from_dict(data)).to_raise(ValueError, match=f"Unknown exigence code: {invalid_code}")
