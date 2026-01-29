from dataclasses import dataclass
from typing import Any

from .exigence import Exigence


@dataclass(frozen=True)
class Langue:
    """
    Attributes
    ----------
    libelle : str | None = None
        Language name
    exigence : Exigence | None = None
        Language requirement
    """

    libelle: str | None = None
    exigence: Exigence | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Langue":
        """Create a Langue from JSON data."""
        exigence_code = data.get("exigence")
        return Langue(
            libelle=data.get("libelle"),
            exigence=Exigence.from_code(exigence_code) if exigence_code is not None else None,
        )
