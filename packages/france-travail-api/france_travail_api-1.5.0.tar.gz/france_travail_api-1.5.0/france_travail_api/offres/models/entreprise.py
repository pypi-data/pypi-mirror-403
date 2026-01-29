from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Entreprise:
    """
    Attributes
    ----------
    nom : str
        Company name
    description : str
        Company description
    logo : str
        Company logo URL
    url : str
        Company URL
    entreprise_adaptee : bool
        Company adapted flag

    Examples
    --------
    >>> Entreprise(nom="Boulanger austral", description="Votre nouvelle boulangerie locale", logo="https://boulanger-austral.net/logo.png", url="https://boulanger-austral.net", entreprise_adaptee=True)
    """

    nom: str | None = None
    description: str | None = None
    logo: str | None = None
    url: str | None = None
    entreprise_adaptee: bool | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Entreprise":
        """Create an Entreprise from JSON data."""
        return Entreprise(
            nom=data.get("nom"),
            description=data.get("description"),
            logo=data.get("logo"),
            url=data.get("url"),
            entreprise_adaptee=data.get("entrepriseAdaptee"),
        )
