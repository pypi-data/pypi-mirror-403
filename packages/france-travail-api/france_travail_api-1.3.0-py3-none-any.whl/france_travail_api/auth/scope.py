from enum import Enum
from typing import Sequence


class Scope(str, Enum):
    """
    Available France Travail API scopes.

    Attributes
    ----------
    OFFRES : str
        Scope for accessing "Offres d'emploi" API.

    References
    ----------
    .. [1] France Travail API Documentation
           https://francetravail.io/data/api
    """

    OFFRES = "api_offresdemploiv2 o2dsoffre"


class Scopes:
    def __init__(self, scopes: Sequence[Scope]) -> None:
        self._scopes = scopes

    def __str__(self) -> str:
        return " ".join(self._scopes)
