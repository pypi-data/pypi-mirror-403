from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LieuTravail:
    """
    Attributes
    ----------
    libelle : str
        Workplace location name
    latitude : float
        Workplace location latitude
    longitude : float
        Workplace location longitude
    code_postal : str
        Workplace location postal code
    commune : str
        Workplace location INSEE code

    Examples
    --------
    >>> LieuTravail(libelle="74 - ANNECY", latitude=45.901584, longitude=6.125296, code_postal="74000", commune="74010")
    """

    libelle: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    code_postal: str | None = None
    commune: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LieuTravail":
        """Create a LieuTravail from JSON data."""
        return LieuTravail(
            libelle=data.get("libelle"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            code_postal=data.get("codePostal"),
            commune=data.get("commune"),
        )
