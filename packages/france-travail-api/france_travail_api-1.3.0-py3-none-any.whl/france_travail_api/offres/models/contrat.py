from enum import Enum


class CodeTypeContrat(Enum):
    """
    Contrat type codes

    Attributes
    ----------
    CDI : Contrat à durée indéterminée
    CDD : Contrat à durée déterminée
    MIS : Mission intérimaire
    SAI : Contrat travail saisonnier
    CCE : Profession commerciale
    FRA : Franchise
    LIB : Profession libérale
    REP : Reprise d'entreprise
    TTI : Contrat travail temporaire insertion
    DDI : Contrat durée déterminée insertion
    DIN : CDI Intérimaire
    DDT : CDD Tremplin
    """

    CDI = "CDI"
    CDD = "CDD"
    MIS = "MIS"
    SAI = "SAI"
    CCE = "CCE"
    FRA = "FRA"
    LIB = "LIB"
    REP = "REP"
    TTI = "TTI"
    DDI = "DDI"
    DIN = "DIN"
    DDT = "DDT"

    def to_api_value(self) -> str:
        return self.value
