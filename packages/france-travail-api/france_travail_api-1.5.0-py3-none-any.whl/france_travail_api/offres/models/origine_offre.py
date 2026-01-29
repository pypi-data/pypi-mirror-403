from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class PartenaireOffre:
    """
    Attributes
    ----------
    nom : str | None = None
        Partner name
    url : str | None = None
        Partner URL
    logo : str | None = None
        Partner logo URL

    Examples
    --------
    >>> PartenaireOffre(nom="PARTENAIRE1", url="https://partenaire-offre.net/boulanger-austral-46841", logo="https://partenaire-offre.net/logo.png")
    """

    nom: str | None = None
    url: str | None = None
    logo: str | None = None


class CodeOrigineOffre(Enum):
    FRANCE_TRAVAIL = "France Travail"
    PARTENAIRE = "Partenaire"

    @staticmethod
    def from_code(code: str) -> "CodeOrigineOffre":
        """Parse origine offre code string to CodeOrigineOffre enum."""
        mapping = {
            "1": CodeOrigineOffre.FRANCE_TRAVAIL,
            "2": CodeOrigineOffre.PARTENAIRE,
        }
        return mapping[code]


@dataclass(frozen=True)
class OrigineOffre:
    """
    Attributes
    ----------
    origine : CodeOrigineOffre | None = None
        Offer origin : France Travail or Partenaire
    url_origine : str | None = None
        Offer origin URL
    partenaires : list[PartenaireOffre] | None = None
        Offer origin partners

    Examples
    --------
    >>> OrigineOffre(origine=CodeOrigineOffre.PARTENAIRE, url_origine="https://partenaire-offre.net/boulanger-austral-46841", partenaires=[PartenaireOffre(nom="PARTENAIRE1", url="https://partenaire-offre.net/boulanger-austral-46841", logo="https://partenaire-offre.net/logo.png")])
    """

    origine: CodeOrigineOffre | None = None
    url_origine: str | None = None
    partenaires: list[PartenaireOffre] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "OrigineOffre":
        """Create an OrigineOffre from JSON data."""
        return OrigineOffre(
            origine=CodeOrigineOffre.from_code(data["origine"]) if data.get("origine") else None,
            url_origine=data.get("urlOrigine"),
            partenaires=None,  # TODO: implement if needed
        )
