from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualitePro:
    """
    Attributes
    ----------
    libelle : str | None = None
        Professional quality name
    description : str | None = None
        Professional quality description
    """

    libelle: str | None = None
    description: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "QualitePro":
        """Create a QualitePro from JSON data."""
        return QualitePro(
            libelle=data.get("libelle"),
            description=data.get("description"),
        )
