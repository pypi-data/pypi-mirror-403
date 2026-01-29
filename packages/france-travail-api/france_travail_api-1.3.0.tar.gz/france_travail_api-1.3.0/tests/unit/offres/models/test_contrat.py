import pytest

from france_travail_api.offres.models.contrat import CodeTypeContrat
from tests.dsl import expect


@pytest.mark.parametrize(
    ("contrat", "expected_value"),
    [
        (CodeTypeContrat.CDI, "CDI"),
        (CodeTypeContrat.CDD, "CDD"),
        (CodeTypeContrat.MIS, "MIS"),
        (CodeTypeContrat.SAI, "SAI"),
        (CodeTypeContrat.CCE, "CCE"),
        (CodeTypeContrat.FRA, "FRA"),
        (CodeTypeContrat.LIB, "LIB"),
        (CodeTypeContrat.REP, "REP"),
        (CodeTypeContrat.TTI, "TTI"),
        (CodeTypeContrat.DDI, "DDI"),
        (CodeTypeContrat.DIN, "DIN"),
        (CodeTypeContrat.DDT, "DDT"),
    ],
)
def test_should_return_api_value(contrat: CodeTypeContrat, expected_value: str) -> None:
    expect(contrat.to_api_value()).to_equal(expected_value)
