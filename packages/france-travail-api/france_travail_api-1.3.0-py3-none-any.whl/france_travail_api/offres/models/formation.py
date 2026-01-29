from dataclasses import dataclass
from typing import Any

from .exigence import Exigence


@dataclass(frozen=True)
class Formation:
    """
    Attributes
    ----------
    code_formation : str | None = None
        Acadmeic training code
    domaine_libelle : str | None = None
        Acadmeic training topic
    niveau_libelle : str | None = None
        Acadmeic training level
    commentaire : str | None = None
        Comment on the academic training
    exigence : Exigence | None = None
        Acadmeic training requirement
    """

    code_formation: str | None = None
    domaine_libelle: str | None = None
    niveau_libelle: str | None = None
    commentaire: str | None = None
    exigence: Exigence | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Formation":
        """Create a Formation from JSON data."""
        exigence_code = data.get("exigence")
        return Formation(
            code_formation=data.get("codeFormation"),
            domaine_libelle=data.get("domaineLibelle"),
            niveau_libelle=data.get("niveauLibelle"),
            commentaire=data.get("commentaire"),
            exigence=Exigence.from_code(exigence_code) if exigence_code is not None else None,
        )
