import pytest

from france_travail_api.offres.models.search_params import (
    DureeHebdo,
    Experience,
    ModeSelectionPartenaires,
    OrigineOffreFilter,
    PeriodeSalaire,
    Qualification,
    Sort,
)
from tests.dsl import expect


@pytest.mark.parametrize(
    ("sort", "expected_value"),
    [
        (Sort.PERTINENCE, "0"),
        (Sort.DATE_CREATION, "1"),
        (Sort.DISTANCE, "2"),
    ],
)
def test_should_return_sort_api_value(sort: Sort, expected_value: str) -> None:
    expect(sort.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("experience", "expected_value"),
    [
        (Experience.NON_PRECISE, "0"),
        (Experience.MOINS_UN_AN, "1"),
        (Experience.UN_A_TROIS_ANS, "2"),
        (Experience.PLUS_DE_TROIS_ANS, "3"),
    ],
)
def test_should_return_experience_api_value(experience: Experience, expected_value: str) -> None:
    expect(experience.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("origine", "expected_value"),
    [
        (OrigineOffreFilter.FRANCE_TRAVAIL, "1"),
        (OrigineOffreFilter.PARTENAIRE, "2"),
    ],
)
def test_should_return_origine_offre_filter_api_value(origine: OrigineOffreFilter, expected_value: str) -> None:
    expect(origine.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("qualification", "expected_value"),
    [
        (Qualification.NON_CADRE, "0"),
        (Qualification.CADRE, "9"),
    ],
)
def test_should_return_qualification_api_value(qualification: Qualification, expected_value: str) -> None:
    expect(qualification.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("periode", "expected_value"),
    [
        (PeriodeSalaire.MENSUEL, "M"),
        (PeriodeSalaire.ANNUEL, "A"),
        (PeriodeSalaire.HORAIRE, "H"),
        (PeriodeSalaire.CACHET, "C"),
    ],
)
def test_should_return_periode_salaire_api_value(periode: PeriodeSalaire, expected_value: str) -> None:
    expect(periode.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("mode", "expected_value"),
    [
        (ModeSelectionPartenaires.INCLUS, "INCLUS"),
        (ModeSelectionPartenaires.EXCLU, "EXCLU"),
    ],
)
def test_should_return_mode_selection_partenaires_api_value(
    mode: ModeSelectionPartenaires, expected_value: str
) -> None:
    expect(mode.to_api_value()).to_equal(expected_value)


@pytest.mark.parametrize(
    ("duree", "expected_value"),
    [
        (DureeHebdo.NON_PRECISE, "0"),
        (DureeHebdo.TEMPS_PLEIN, "1"),
        (DureeHebdo.TEMPS_PARTIEL, "2"),
    ],
)
def test_should_return_duree_hebdo_api_value(duree: DureeHebdo, expected_value: str) -> None:
    expect(duree.to_api_value()).to_equal(expected_value)
