from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Contact:
    """
    Attributes
    ----------
    nom : str | None = None
        Contact name
    coordonnees1 : str | None = None
        Contact address 1
    coordonnees2 : str | None = None
        Contact address 2
    coordonnees3 : str | None = None
        Contact address 3
    telephone : str | None = None
        Contact phone number
    courriel : str | None = None
        Note: The email field is no longer displayed for security reasons, the field now provides a link to the offer on the FranceTravail.fr website to know the procedures for applying
    commentaire : str | None = None
        Contact comment
    url_recruteur : str | None = None
        Contact recruiter URL
    url_postulation : str | None = None
        Contact postulation URL

    Examples
    --------
    >>> Contact(nom="Etienne Dupont", coordonnees1="12 impasse du caillou", coordonnees2="12 impasse du caillou", coordonnees3="12 impasse du caillou", telephone="06 12 34 56 78", courriel="Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX", commentaire="A contacter après 19h", url_recruteur="https://boulanger-austral.net", url_postulation="https://boulanger-austral.net/carrieres")
    """

    nom: str | None = None
    coordonnees1: str | None = None
    coordonnees2: str | None = None
    coordonnees3: str | None = None
    telephone: str | None = None
    courriel: str | None = None
    commentaire: str | None = None
    url_recruteur: str | None = None
    url_postulation: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Contact":
        """Create a Contact from JSON data."""
        return Contact(
            nom=data.get("nom"),
            coordonnees1=data.get("coordonnees1"),
            coordonnees2=data.get("coordonnees2"),
            coordonnees3=data.get("coordonnees3"),
            telephone=data.get("telephone"),
            courriel=data.get("courriel"),
            commentaire=data.get("commentaire"),
            url_recruteur=data.get("urlRecruteur"),
            url_postulation=data.get("urlPostulation"),
        )
