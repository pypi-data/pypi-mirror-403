from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComplementSalaire:
    """
    Attributes
    ----------
    code : str | None = None
        Salary information complement code
    libelle : str | None = None
        Salary information complement name

    Examples
    --------
    >>> ComplementSalaire(code="14", libelle="Véhicule de fonction")
    """

    code: str | None = None
    libelle: str | None = None


@dataclass(frozen=True)
class Salaire:
    """
    Attributes
    ----------
    libelle : str | None = None
        Salary information description
    commentaire : str | None = None
        Salary information comment
    complement1 : str | None = None
        Salary information complement 1
    complement2 : str | None = None
        Salary information complement 2
    liste_complements : list[ComplementSalaire] | None = None
        Salary information complement list (max 5)

    Examples
    --------
    >>> Salaire(libelle="Mensuel de 1923.00 Euros sur 12 mois", commentaire="Selon expérience", complement1="Véhicule de fonction", complement2="Prime de vacances", liste_complements=[ComplementSalaire(code="14", libelle="Véhicule de fonction"), ComplementSalaire(code="15", libelle="Prime de vacances"), ComplementSalaire(code="16", libelle="Prime de vacances")])
    """

    libelle: str | None = None
    commentaire: str | None = None
    complement1: str | None = None
    complement2: str | None = None
    liste_complements: list[ComplementSalaire] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Salaire":
        """Create a Salaire from JSON data."""
        return Salaire(
            libelle=data.get("libelle"),
            commentaire=data.get("commentaire"),
            complement1=data.get("complement1"),
            complement2=data.get("complement2"),
            liste_complements=None,  # TODO: implement if needed
        )
