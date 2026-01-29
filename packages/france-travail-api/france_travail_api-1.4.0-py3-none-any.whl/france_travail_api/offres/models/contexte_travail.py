from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContexteTravail:
    """
    Work context (hours and conditions)

    Attributes
    ----------
    horaires : list[str] | None = None
        Work context hours
    conditions_exercice : list[str] | None = None
        Work context conditions

    Examples
    --------
    >>> ContexteTravail(horaires=["35H Travail le samedi"], conditions_exercice=["Port de tenue professionnelle ou d'uniforme"])
    """

    horaires: list[str] | None = None
    conditions_exercice: list[str] | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ContexteTravail":
        """Create a ContexteTravail from JSON data."""
        return ContexteTravail(
            horaires=list(data["horaires"]) if data.get("horaires") is not None else None,
            conditions_exercice=list(data["conditionsExercice"])
            if data.get("conditionsExercice") is not None
            else None,
        )
