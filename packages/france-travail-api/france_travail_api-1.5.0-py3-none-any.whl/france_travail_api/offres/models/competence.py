from dataclasses import dataclass
from typing import Any

from .exigence import Exigence


@dataclass(frozen=True)
class Competence:
    """
    Attributes
    ----------
    code : str | None = None
        Competence code
    libelle : str | None = None
        Competence name
    exigence : Exigence | None = None
        Competence requirement
    """

    code: str | None = None
    libelle: str | None = None
    exigence: Exigence | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Competence":
        """Create a Competence from JSON data."""
        exigence_value = data.get("exigence")
        return Competence(
            code=data.get("code"),
            libelle=data.get("libelle"),
            exigence=Exigence.from_code(exigence_value) if isinstance(exigence_value, str) else None,
        )
