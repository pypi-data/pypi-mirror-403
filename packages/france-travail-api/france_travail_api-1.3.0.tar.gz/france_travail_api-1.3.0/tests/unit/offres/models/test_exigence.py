import pytest

from france_travail_api.offres.models.exigence import Exigence
from tests.dsl import expect


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("E", Exigence.OBLIGATOIRE),
        ("S", Exigence.SOUHAITE),
    ],
)
def test_from_code_should_return_correct_exigence(code: str, expected: Exigence) -> None:
    expect(Exigence.from_code(code)).to_equal(expected)


@pytest.mark.parametrize("invalid_code", ["X", "INVALID", "123", ""])
def test_from_code_should_raise_value_error_when_code_is_unknown(invalid_code: str) -> None:
    expect(lambda: Exigence.from_code(invalid_code)).to_raise(
        ValueError, match=f"Unknown exigence code: {invalid_code}"
    )
