from dataclasses import dataclass
from typing import Any

from .exigence import Exigence


@dataclass(frozen=True)
class Permis:
    """
    Driving license information

    Attributes
    ----------
    libelle : str | None = None
        Driving license name
    exigence : str | None = None
        Driving license requirement
    """

    libelle: str | None = None
    exigence: Exigence | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Permis":
        """Create a Permis from JSON data."""
        exigence_code = data.get("exigence")
        return Permis(
            libelle=data.get("libelle"),
            exigence=Exigence.from_code(exigence_code) if exigence_code is not None else None,
        )
