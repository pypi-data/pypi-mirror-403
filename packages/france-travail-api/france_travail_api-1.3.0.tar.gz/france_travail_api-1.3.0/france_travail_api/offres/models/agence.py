from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Agence:
    """
    France Travail agency

    Attributes
    ----------
    telephone : str | None = None
        Agency phone number
    courriel : str | None = None
        Note: The France Travail agency email is no longer displayed for security reasons, the field now provides a link to the offer on the FranceTravail.fr website to know the procedures for applying

    Examples
    --------
    >>> Agence(telephone="06 12 34 56 78", courriel="Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX")
    """

    telephone: str | None = None
    courriel: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Agence":
        """Create an Agence from JSON data."""
        return Agence(
            telephone=data.get("telephone"),
            courriel=data.get("courriel"),
        )
