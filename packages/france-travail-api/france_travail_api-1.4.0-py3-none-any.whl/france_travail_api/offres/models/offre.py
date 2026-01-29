import datetime
from dataclasses import dataclass, field
from typing import Any

from .agence import Agence
from .competence import Competence
from .contact import Contact
from .contexte_travail import ContexteTravail
from .contrat import CodeTypeContrat
from .entreprise import Entreprise
from .experience import ExperienceExigee
from .formation import Formation
from .langue import Langue
from .lieu_travail import LieuTravail
from .origine_offre import OrigineOffre
from .permis import Permis
from .qualite_pro import QualitePro
from .salaire import Salaire


def _parse_date(date_str: str) -> datetime.datetime:
    """Parse ISO 8601 date string to datetime object."""
    return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Offre:
    """
    Job offer

    Attributes
    ----------
    id : str | None = None
        Job offer identifier
    intitule : str | None = None
        Job offer title
    description : str | None = None
        Job offer description
    date_creation : datetime.datetime | None = None
        Job offer creation date
    date_actualisation : datetime.datetime | None = None
        Job offer last update date
    lieu_travail : LieuTravail | None = None
        Workplace location
    rome_code : str | None = None
        Job offer ROME code
    rome_libelle : str | None = None
        ROME code label
    appellation_libelle : str | None = None
        ROME appellation label
    entreprise : Entreprise | None = None
        Company information
    type_contrat : CodeTypeContrat | None = None
        Contract type code (CDI, CDD, etc.)
    type_contrat_libelle : str | None = None
        Contract type label
    nature_contrat : str | None = None
        Contract nature (apprenticeship contract, etc.)
    experience_exige : ExperienceExigee | None = None
        Required experience level (beginner accepted, experience required, etc.)
    experience_libelle : str | None = None
        Experience label
    experience_commentaire : str | None = None
        Experience comment
    formations : list[Formation] | None = None
        Required formations
    langues : list[Langue] | None = None
        Required languages
    permis : list[Permis] | None = None
        Required permits
    outils_bureautiques : list[str] | None = None
        Office tools used
    competences : list[Competence] | None = None
        Required competences
    salaire : Salaire | None = None
        Salary information
    duree_travail_libelle : str | None = None
        Work duration label
    duree_travail_libelle_converti : str | None = None
        Full time or part time
    complement_exercice : str | None = None
        Additional work information
    condition_exercice : str | None = None
        Work conditions
    alternance : bool | None = None
        True if the offer is for alternance
    contact : Contact | None = None
        Contact information
    agence : Agence | None = None
        France Travail agency information
    nombre_postes : int | None = None
        Number of available positions for this offer
    accessible_th : bool | None = None
        True if the offer is accessible to disabled workers
    deplacement_code : str | None = None
        Travel frequency code
    deplacement_libelle : str | None = None
        Travel description
    qualification_code : str | None = None
        Position qualification code (1 - manœuvre, ..., 8 - agent de maitrise, 9 - cadre)
    qualification_libelle : str | None = None
        Position qualification label
    code_naf : str | None = None
        NAF code (APE code)
    secteur_activite : str | None = None
        NAF division (first two digits of NAF code)
    secteur_activite_libelle : str | None = None
        Business sector of the offer
    qualites_professionnelles : list[QualitePro] | None = None
        Professional qualities
    tranche_effectif_etab : str | None = None
        Company size range. Only present when the company is identified and has filled in its size range (only 20% of offers)
    origine_offre : OrigineOffre | None = None
        Offer origin information
    offres_manque_candidats : bool | None = None
        True if the offer is difficult to fill
    contexte_travail : ContexteTravail | None = None
        Work context (hours and conditions)
    entreprise_adaptee : bool | None = None
        True if the company allows a disabled worker to carry out a professional activity in conditions adapted to their capacities
    employeur_handi_engage : bool | None = None
        True if the employer is recognized by France Travail, Cap emploi and its partners for its concrete actions in favor of recruitment, integration and support of its disabled employees

    Examples
    --------
    >>> Offre(
    ...     id="048KLTP",
    ...     intitule="Boulanger / Boulangère (H/F)",
    ...     description="Nous recherchons un/e Boulanger/ère pour notre nouveau magasin.",
    ...     date_creation=datetime.datetime(2022, 10, 23, 8, 15, 42),
    ...     type_contrat=CodeTypeContrat.CDD,
    ...     type_contrat_libelle="CDD - 6 Mois",
    ...     experience_exige=ExperienceExigee.DEBUTANT_ACCEPTE,
    ...     alternance=False,
    ...     nombre_postes=3,
    ...     accessible_th=True
    ... )

    References
    ----------
    .. [1] France Travail API Documentation - Offres d'emploi - Schemas - Offre
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/schemas/Offre
    """

    id: str | None = None
    intitule: str | None = None
    description: str | None = None
    date_creation: datetime.datetime | None = None
    date_actualisation: datetime.datetime | None = None
    lieu_travail: LieuTravail | None = None
    rome_code: str | None = None
    rome_libelle: str | None = None
    appellation_libelle: str | None = None
    entreprise: Entreprise | None = None
    type_contrat: CodeTypeContrat | None = None
    type_contrat_libelle: str | None = None
    nature_contrat: str | None = None
    experience_exige: ExperienceExigee | None = None
    experience_libelle: str | None = None
    experience_commentaire: str | None = None
    formations: list[Formation] = field(default_factory=list)
    langues: list[Langue] = field(default_factory=list)
    permis: list[Permis] = field(default_factory=list)
    outils_bureautiques: list[str] | None = None
    competences: list[Competence] | None = None
    salaire: Salaire | None = None
    duree_travail_libelle: str | None = None
    duree_travail_libelle_converti: str | None = None
    complement_exercice: str | None = None
    condition_exercice: str | None = None
    alternance: bool | None = None
    contact: Contact | None = None
    agence: Agence | None = None
    nombre_postes: int | None = None
    accessible_th: bool | None = None
    deplacement_code: str | None = None
    deplacement_libelle: str | None = None
    qualification_code: str | None = None
    qualification_libelle: str | None = None
    code_naf: str | None = None
    secteur_activite: str | None = None
    secteur_activite_libelle: str | None = None
    qualites_professionnelles: list[QualitePro] = field(default_factory=list)
    tranche_effectif_etab: str | None = None
    origine_offre: OrigineOffre | None = None
    offres_manque_candidats: bool | None = None
    contexte_travail: ContexteTravail | None = None
    entreprise_adaptee: bool | None = None
    employeur_handi_engage: bool | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Offre":
        """Create an Offre from JSON data.

        Parameters
        ----------
        data : dict[str, Any]
            JSON data from the France Travail API

        Returns
        -------
        Offre
            Job offer object
        """
        return Offre(
            id=data.get("id"),
            intitule=data.get("intitule"),
            description=data.get("description"),
            date_creation=_parse_date(data["dateCreation"]) if data.get("dateCreation") else None,
            date_actualisation=_parse_date(data["dateActualisation"]) if data.get("dateActualisation") else None,
            lieu_travail=LieuTravail.from_dict(data["lieuTravail"]) if data.get("lieuTravail") else None,
            rome_code=data.get("romeCode"),
            rome_libelle=data.get("romeLibelle"),
            appellation_libelle=data.get("appellationlibelle"),
            entreprise=Entreprise.from_dict(data["entreprise"]) if data.get("entreprise") else None,
            type_contrat=CodeTypeContrat(data["typeContrat"]) if data.get("typeContrat") else None,
            type_contrat_libelle=data.get("typeContratLibelle"),
            nature_contrat=data.get("natureContrat"),
            experience_exige=ExperienceExigee.from_code(data["experienceExige"])
            if data.get("experienceExige")
            else None,
            experience_libelle=data.get("experienceLibelle"),
            experience_commentaire=data.get("experienceCommentaire"),
            formations=[Formation.from_dict(formation_dict) for formation_dict in data.get("formations", [])],
            langues=[Langue.from_dict(langue_dict) for langue_dict in data.get("langues", [])],
            permis=[Permis.from_dict(permis_dict) for permis_dict in data.get("permis", [])],
            competences=[Competence.from_dict(competence_dict) for competence_dict in data.get("competences", [])],
            outils_bureautiques=data.get("outilsBureautiques", []),
            salaire=Salaire.from_dict(data["salaire"]) if data.get("salaire") else None,
            duree_travail_libelle=data.get("dureeTravailLibelle"),
            duree_travail_libelle_converti=data.get("dureeTravailLibelleConverti"),
            complement_exercice=data.get("complementExercice"),
            condition_exercice=data.get("conditionExercice"),
            alternance=data.get("alternance"),
            contact=Contact.from_dict(data["contact"]) if data.get("contact") else None,
            agence=Agence.from_dict(data["agence"]) if data.get("agence") else None,
            nombre_postes=data.get("nombrePostes"),
            accessible_th=data.get("accessibleTH"),
            deplacement_code=data.get("deplacementCode"),
            deplacement_libelle=data.get("deplacementLibelle"),
            qualification_code=data.get("qualificationCode"),
            qualification_libelle=data.get("qualificationLibelle"),
            code_naf=data.get("codeNAF"),
            secteur_activite=data.get("secteurActivite"),
            secteur_activite_libelle=data.get("secteurActiviteLibelle"),
            qualites_professionnelles=[
                QualitePro.from_dict(qualite_pro_dict) for qualite_pro_dict in data.get("qualitesProfessionnelles", [])
            ],
            tranche_effectif_etab=data.get("trancheEffectifEtab"),
            origine_offre=OrigineOffre.from_dict(data["origineOffre"]) if data.get("origineOffre") else None,
            offres_manque_candidats=data.get("offresManqueCandidats"),
            contexte_travail=ContexteTravail.from_dict(data["contexteTravail"])
            if data.get("contexteTravail")
            else None,
            entreprise_adaptee=data.get("entrepriseAdaptee"),
            employeur_handi_engage=data.get("employeurHandiEngage"),
        )
