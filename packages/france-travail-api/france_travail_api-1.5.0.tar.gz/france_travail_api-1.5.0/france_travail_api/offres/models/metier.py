from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Metier:
    """
    Job occupation from France Travail ROME referential.

    Attributes
    ----------
    code : str | None = None
        Metier ROME code (e.g., "M1805" for Études et développement informatique)
    libelle : str | None = None
        Metier label/name (e.g., "Études et développement informatique")
    """

    code: str | None = None
    libelle: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Metier":
        """
        Create a Metier from JSON data.

        Parameters
        ----------
        data : dict[str, Any]
            Dictionary containing metier data from France Travail API

        Returns
        -------
        Metier
            Metier instance created from the provided data
        """
        return Metier(
            code=data.get("code"),
            libelle=data.get("libelle"),
        )
