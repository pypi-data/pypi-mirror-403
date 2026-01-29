from enum import Enum


class Exigence(Enum):
    """
    Exigence codes

    Attributes
    ----------
    OBLIGATOIRE : Exigence
        Obligatoire
    SOUHAITE : Exigence
        Souhaité
    """

    OBLIGATOIRE = "OBLIGATOIRE"
    SOUHAITE = "SOUHAITE"

    @staticmethod
    def from_code(code: str) -> "Exigence | None":
        """Parse exigence code to Exigence enum."""
        match code:
            case "E":
                return Exigence.OBLIGATOIRE
            case "S":
                return Exigence.SOUHAITE
            case _:
                raise ValueError(f"Unknown exigence code: {code}")
