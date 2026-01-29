from enum import Enum


class Sort(Enum):
    """
    Sorting method for job offer search results.

    Attributes
    ----------
    PERTINENCE : Relevance (descending), distance (ascending), creation date (descending)
    DATE_CREATION : Creation date (descending), relevance (descending), distance (ascending)
    DISTANCE : Distance (ascending), relevance (descending), creation date (descending)
    """

    PERTINENCE = "Pertinence décroissante, distance croissante, date de création décroissante"
    DATE_CREATION = "Date de création décroissante, pertinence décroissante, distance croissante"
    DISTANCE = "Distance croissante, pertinence décroissante, date de création décroissante"

    def to_api_value(self) -> str:
        mapping = {
            Sort.PERTINENCE: "0",
            Sort.DATE_CREATION: "1",
            Sort.DISTANCE: "2",
        }
        return mapping[self]


class Experience(Enum):
    """
    Experience level required for the job.

    Attributes
    ----------
    NON_PRECISE : Not specified
    MOINS_UN_AN : Less than 1 year
    UN_A_TROIS_ANS : 1 to 3 years
    PLUS_DE_TROIS_ANS : More than 3 years
    """

    NON_PRECISE = "Non précisé"
    MOINS_UN_AN = "Moins d'un an"
    UN_A_TROIS_ANS = "De 1 à 3 ans"
    PLUS_DE_TROIS_ANS = "Plus de 3 ans"

    def to_api_value(self) -> str:
        mapping = {
            Experience.NON_PRECISE: "0",
            Experience.MOINS_UN_AN: "1",
            Experience.UN_A_TROIS_ANS: "2",
            Experience.PLUS_DE_TROIS_ANS: "3",
        }
        return mapping[self]


class OrigineOffreFilter(Enum):
    """
    Origin filter for job offers.

    Attributes
    ----------
    FRANCE_TRAVAIL : Offers from France Travail
    PARTENAIRE : Offers from partners
    """

    FRANCE_TRAVAIL = "France Travail"
    PARTENAIRE = "Partenaire"

    def to_api_value(self) -> str:
        mapping = {
            OrigineOffreFilter.FRANCE_TRAVAIL: "1",
            OrigineOffreFilter.PARTENAIRE: "2",
        }
        return mapping[self]


class Qualification(Enum):
    """
    Qualification level for the position.

    Attributes
    ----------
    NON_CADRE : Non-executive
    CADRE : Executive
    """

    NON_CADRE = "Non-cadre"
    CADRE = "Cadre"

    def to_api_value(self) -> str:
        mapping = {
            Qualification.NON_CADRE: "0",
            Qualification.CADRE: "9",
        }
        return mapping[self]


class PeriodeSalaire(Enum):
    """
    Salary period for minimum salary filter.

    Attributes
    ----------
    MENSUEL : Monthly
    ANNUEL : Annual
    HORAIRE : Hourly
    CACHET : Per performance (for artists)
    """

    MENSUEL = "Mensuel"
    ANNUEL = "Annuel"
    HORAIRE = "Horaire"
    CACHET = "Cachet"

    def to_api_value(self) -> str:
        mapping = {
            PeriodeSalaire.MENSUEL: "M",
            PeriodeSalaire.ANNUEL: "A",
            PeriodeSalaire.HORAIRE: "H",
            PeriodeSalaire.CACHET: "C",
        }
        return mapping[self]


class ModeSelectionPartenaires(Enum):
    """
    Partner selection mode.

    Attributes
    ----------
    INCLUS : Include specified partners
    EXCLU : Exclude specified partners
    """

    INCLUS = "Inclus"
    EXCLU = "Exclu"

    def to_api_value(self) -> str:
        mapping = {
            ModeSelectionPartenaires.INCLUS: "INCLUS",
            ModeSelectionPartenaires.EXCLU: "EXCLU",
        }
        return mapping[self]


class DureeHebdo(Enum):
    """
    Weekly work duration type.

    Attributes
    ----------
    NON_PRECISE : Not specified
    TEMPS_PLEIN : Full-time
    TEMPS_PARTIEL : Part-time
    """

    NON_PRECISE = "Non précisé"
    TEMPS_PLEIN = "Temps plein"
    TEMPS_PARTIEL = "Temps partiel"

    def to_api_value(self) -> str:
        mapping = {
            DureeHebdo.NON_PRECISE: "0",
            DureeHebdo.TEMPS_PLEIN: "1",
            DureeHebdo.TEMPS_PARTIEL: "2",
        }
        return mapping[self]
