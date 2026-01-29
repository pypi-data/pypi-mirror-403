import http

from france_travail_api._url import FranceTravailUrl
from france_travail_api.auth._credentials import FranceTravailCredentials
from france_travail_api.exceptions import OffreNotFoundException
from france_travail_api.http_transport._http_client import HttpClient
from france_travail_api.http_transport._http_response import HTTPResponse
from france_travail_api.offres.models import Offre
from france_travail_api.offres.models.contrat import CodeTypeContrat
from france_travail_api.offres.models.experience import ExperienceExigee
from france_travail_api.offres.models.search_params import (
    DureeHebdo,
    Experience,
    ModeSelectionPartenaires,
    OrigineOffreFilter,
    PeriodeSalaire,
    Qualification,
    Sort,
)

JOB_OFFER_SEARCH_API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
JOB_OFFER_GET_API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres"


class FranceTravailOffresClient:
    def __init__(self, credentials: FranceTravailCredentials, http_client: HttpClient) -> None:
        self._credentials = credentials
        self._http_client = http_client

    def search(
        self,
        mots_cles: str,
        sort: Sort | None = None,
        domaine: str | None = None,
        code_rome: str | None = None,
        appellation: str | None = None,
        theme: str | None = None,
        secteur_activite: str | None = None,
        code_naf: str | None = None,
        experience: Experience | None = None,
        type_contrat: CodeTypeContrat | None = None,
        nature_contrat: str | None = None,
        origine_offre: OrigineOffreFilter | None = None,
        qualification: Qualification | None = None,
        temps_plein: bool | None = None,
        commune: str | None = None,
        distance: int | None = None,
        departement: str | None = None,
        inclure_limitrophes: bool | None = None,
        region: str | None = None,
        pays_continent: str | None = None,
        niveau_formation: str | None = None,
        permis: str | None = None,
        salaire_min: str | None = None,
        periode_salaire: PeriodeSalaire | None = None,
        acces_travailleur_handicape: bool | None = None,
        publiee_depuis: int | None = None,
        min_creation_date: str | None = None,
        max_creation_date: str | None = None,
        offres_mrs: bool | None = None,
        experience_exigence: ExperienceExigee | None = None,
        grand_domaine: str | None = None,
        partenaires: str | None = None,
        mode_selection_partenaires: ModeSelectionPartenaires | None = None,
        duree_hebdo_min: str | None = None,
        duree_hebdo_max: str | None = None,
        duree_contrat_min: str | None = None,
        duree_contrat_max: str | None = None,
        duree_hebdo: DureeHebdo | None = None,
        offres_manque_candidats: bool | None = None,
        entreprises_adaptees: bool | None = None,
        employeurs_handi_engages: bool | None = None,
        range_param: str | None = None,
    ) -> list[Offre]:
        """Search for job offers.

        Parameters
        ----------
        mots_cles : str
            Keywords to search for
        sort : Sort, optional
            Sorting method (Sort.PERTINENCE, Sort.DATE_CREATION, Sort.DISTANCE)
        domaine : str, optional
            Job domain code
        code_rome : str, optional
            ROME code (up to 200 values, comma-separated)
        appellation : str, optional
            ROME appellation code
        theme : str, optional
            ROME theme code
        secteur_activite : str, optional
            Activity sector (NAF division, up to 2 values)
        code_naf : str, optional
            NAF code (format 99.99X, up to 2 values)
        experience : Experience, optional
            Experience level (Experience.NON_PRECISE, Experience.MOINS_UN_AN, etc.)
        type_contrat : CodeTypeContrat, optional
            Contract type (CodeTypeContrat.CDI, CodeTypeContrat.CDD, etc.)
        nature_contrat : str, optional
            Contract nature code
        origine_offre : OrigineOffreFilter, optional
            Offer origin filter (OrigineOffreFilter.FRANCE_TRAVAIL, OrigineOffreFilter.PARTENAIRE)
        qualification : Qualification, optional
            Qualification level (Qualification.NON_CADRE, Qualification.CADRE)
        temps_plein : bool, optional
            Full-time or part-time
        commune : str, optional
            INSEE commune code (up to 5 values, comma-separated)
        distance : int, optional
            Distance radius in km around the commune
        departement : str, optional
            Department code (up to 5 values, comma-separated)
        inclure_limitrophes : bool, optional
            Include neighboring departments
        region : str, optional
            Region code
        pays_continent : str, optional
            Country or continent code
        niveau_formation : str, optional
            Education level code
        permis : str, optional
            Driving license code
        salaire_min : str, optional
            Minimum salary (requires periode_salaire)
        periode_salaire : PeriodeSalaire, optional
            Salary period (PeriodeSalaire.MENSUEL, PeriodeSalaire.ANNUEL, etc.)
        acces_travailleur_handicape : bool, optional
            Accessible to workers with disabilities
        publiee_depuis : int, optional
            Published within last X days
        min_creation_date : str, optional
            Minimum creation date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        max_creation_date : str, optional
            Maximum creation date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        offres_mrs : bool, optional
            Only offers with simulation-based recruitment method
        experience_exigence : ExperienceExigee, optional
            Experience requirement (ExperienceExigee.DEBUTANT_ACCEPTE, etc.)
        grand_domaine : str, optional
            Major domain code
        partenaires : str, optional
            Partner codes list
        mode_selection_partenaires : ModeSelectionPartenaires, optional
            Partner selection mode (ModeSelectionPartenaires.INCLUS, ModeSelectionPartenaires.EXCLU)
        duree_hebdo_min : str, optional
            Minimum weekly duration (format HHMM)
        duree_hebdo_max : str, optional
            Maximum weekly duration (format HHMM)
        duree_contrat_min : str, optional
            Minimum contract duration in months (0-99)
        duree_contrat_max : str, optional
            Maximum contract duration in months (0-99)
        duree_hebdo : DureeHebdo, optional
            Weekly duration type (DureeHebdo.NON_PRECISE, DureeHebdo.TEMPS_PLEIN, etc.)
        offres_manque_candidats : bool, optional
            Filter offers difficult to fill
        entreprises_adaptees : bool, optional
            Filter adapted companies for workers with disabilities
        employeurs_handi_engages : bool, optional
            Filter employers committed to hiring workers with disabilities
        range_param : str, optional
            Pagination range (format: p-d, limited to 150 results)

        Returns
        -------
        list[Offre]
            List of job offers matching the search criteria

        Examples
        --------
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> client.search(mots_cles="développeur python", commune="75056", distance=10, type_contrat="CDI")
        [Offre(id="201WLXK", intitule="Développeur backend Python/Django (H/F)", ...)]

        References
        ----------
        .. [1] France Travail API Documentation - Offres d'emploi - Rechercher des offres
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererListeOffre
        """
        params = locals().copy()
        params.pop("self")
        params = self._convert_enums_to_api_values(params)

        url = self._build_search_url(params)
        response_body = self._execute_search_request(url)
        return [Offre.from_dict(offre_json) for offre_json in response_body.get("resultats", [])]

    async def search_async(
        self,
        mots_cles: str,
        sort: Sort | None = None,
        domaine: str | None = None,
        code_rome: str | None = None,
        appellation: str | None = None,
        theme: str | None = None,
        secteur_activite: str | None = None,
        code_naf: str | None = None,
        experience: Experience | None = None,
        type_contrat: CodeTypeContrat | None = None,
        nature_contrat: str | None = None,
        origine_offre: OrigineOffreFilter | None = None,
        qualification: Qualification | None = None,
        temps_plein: bool | None = None,
        commune: str | None = None,
        distance: int | None = None,
        departement: str | None = None,
        inclure_limitrophes: bool | None = None,
        region: str | None = None,
        pays_continent: str | None = None,
        niveau_formation: str | None = None,
        permis: str | None = None,
        salaire_min: str | None = None,
        periode_salaire: PeriodeSalaire | None = None,
        acces_travailleur_handicape: bool | None = None,
        publiee_depuis: int | None = None,
        min_creation_date: str | None = None,
        max_creation_date: str | None = None,
        offres_mrs: bool | None = None,
        experience_exigence: ExperienceExigee | None = None,
        grand_domaine: str | None = None,
        partenaires: str | None = None,
        mode_selection_partenaires: ModeSelectionPartenaires | None = None,
        duree_hebdo_min: str | None = None,
        duree_hebdo_max: str | None = None,
        duree_contrat_min: str | None = None,
        duree_contrat_max: str | None = None,
        duree_hebdo: DureeHebdo | None = None,
        offres_manque_candidats: bool | None = None,
        entreprises_adaptees: bool | None = None,
        employeurs_handi_engages: bool | None = None,
        range_param: str | None = None,
    ) -> list[Offre]:
        """Search for job offers asynchronously.

        Parameters
        ----------
        mots_cles : str
            Keywords to search for
        sort : Sort, optional
            Sorting method (Sort.PERTINENCE, Sort.DATE_CREATION, Sort.DISTANCE)
        domaine : str, optional
            Job domain code
        code_rome : str, optional
            ROME code (up to 200 values, comma-separated)
        appellation : str, optional
            ROME appellation code
        theme : str, optional
            ROME theme code
        secteur_activite : str, optional
            Activity sector (NAF division, up to 2 values)
        code_naf : str, optional
            NAF code (format 99.99X, up to 2 values)
        experience : Experience, optional
            Experience level (Experience.NON_PRECISE, Experience.MOINS_UN_AN, etc.)
        type_contrat : CodeTypeContrat, optional
            Contract type (CodeTypeContrat.CDI, CodeTypeContrat.CDD, etc.)
        nature_contrat : str, optional
            Contract nature code
        origine_offre : OrigineOffreFilter, optional
            Offer origin filter (OrigineOffreFilter.FRANCE_TRAVAIL, OrigineOffreFilter.PARTENAIRE)
        qualification : Qualification, optional
            Qualification level (Qualification.NON_CADRE, Qualification.CADRE)
        temps_plein : bool, optional
            Full-time or part-time
        commune : str, optional
            INSEE commune code (up to 5 values, comma-separated)
        distance : int, optional
            Distance radius in km around the commune
        departement : str, optional
            Department code (up to 5 values, comma-separated)
        inclure_limitrophes : bool, optional
            Include neighboring departments
        region : str, optional
            Region code
        pays_continent : str, optional
            Country or continent code
        niveau_formation : str, optional
            Education level code
        permis : str, optional
            Driving license code
        salaire_min : str, optional
            Minimum salary (requires periode_salaire)
        periode_salaire : PeriodeSalaire, optional
            Salary period (PeriodeSalaire.MENSUEL, PeriodeSalaire.ANNUEL, etc.)
        acces_travailleur_handicape : bool, optional
            Accessible to workers with disabilities
        publiee_depuis : int, optional
            Published within last X days
        min_creation_date : str, optional
            Minimum creation date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        max_creation_date : str, optional
            Maximum creation date (format: yyyy-MM-dd'T'HH:mm:ss'Z')
        offres_mrs : bool, optional
            Only offers with simulation-based recruitment method
        experience_exigence : ExperienceExigee, optional
            Experience requirement (ExperienceExigee.DEBUTANT_ACCEPTE, etc.)
        grand_domaine : str, optional
            Major domain code
        partenaires : str, optional
            Partner codes list
        mode_selection_partenaires : ModeSelectionPartenaires, optional
            Partner selection mode (ModeSelectionPartenaires.INCLUS, ModeSelectionPartenaires.EXCLU)
        duree_hebdo_min : str, optional
            Minimum weekly duration (format HHMM)
        duree_hebdo_max : str, optional
            Maximum weekly duration (format HHMM)
        duree_contrat_min : str, optional
            Minimum contract duration in months (0-99)
        duree_contrat_max : str, optional
            Maximum contract duration in months (0-99)
        duree_hebdo : DureeHebdo, optional
            Weekly duration type (DureeHebdo.NON_PRECISE, DureeHebdo.TEMPS_PLEIN, etc.)
        offres_manque_candidats : bool, optional
            Filter offers difficult to fill
        entreprises_adaptees : bool, optional
            Filter adapted companies for workers with disabilities
        employeurs_handi_engages : bool, optional
            Filter employers committed to hiring workers with disabilities
        range_param : str, optional
            Pagination range (format: p-d, limited to 150 results)

        Returns
        -------
        list[Offre]
            List of job offers matching the search criteria

        Examples
        --------
        >>> import asyncio
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> asyncio.run(client.search_async(mots_cles="développeur python", commune="75056", distance=10, type_contrat="CDI"))
        [Offre(id="201WLXK", intitule="Développeur backend Python/Django (H/F)", ...)]

        References
        ----------
        .. [1] France Travail API Documentation - Offres d'emploi - Rechercher des offres
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererListeOffre
        """
        params = locals().copy()
        params.pop("self")
        params = self._convert_enums_to_api_values(params)

        url = self._build_search_url(params)
        response_body = await self._execute_search_request_async(url)
        return [Offre.from_dict(offre_json) for offre_json in response_body.get("resultats", [])]

    def get(self, offer_id: str) -> Offre:
        """Get a job offer by its ID.

        Parameters
        ----------
        offer_id : str
            Job offer ID (e.g., "048KLTP").

        Returns
        -------
        Offre
            The job offer with the specified ID.

        Raises
        ------
        OffreNotFoundException
            If no job offer with the specified ID exists.

        Examples
        --------
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> client.get(offer_id="048KLTP")
        Offre(id="048KLTP", intitule="Développeur Python (H/F)", ...)

        References
        ----------
        .. [1] France Travail API Documentation - Offres d'emploi - Consulter un détail d'offre
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererOffre
        """
        url = self._build_get_url(offer_id)
        response = self._execute_get_request(url)
        return self._parse_get_response(response, offer_id)

    async def get_async(self, offer_id: str) -> Offre:
        """Get a job offer by its ID asynchronously.

        Parameters
        ----------
        offer_id : str
            Job offer ID (e.g., "048KLTP").

        Returns
        -------
        Offre
            The job offer with the specified ID.

        Raises
        ------
        OffreNotFoundException
            If no job offer with the specified ID exists.

        Examples
        --------
        >>> import asyncio
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> asyncio.run(client.get_async(offer_id="048KLTP"))
        Offre(id="048KLTP", intitule="Développeur Python (H/F)", ...)

        References
        ----------
        .. [1] France Travail API Documentation - Offres d'emploi - Consulter un détail d'offre
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererOffre
        """
        url = self._build_get_url(offer_id)
        response = await self._execute_get_request_async(url)
        return self._parse_get_response(response, offer_id)

    def _build_get_url(self, offer_id: str) -> str:
        return f"{JOB_OFFER_GET_API_URL}/{offer_id}"

    def _execute_get_request(self, url: str) -> HTTPResponse:
        return self._http_client.get(
            url=url,
            headers=self._credentials.to_authorization_header(),
        )

    async def _execute_get_request_async(self, url: str) -> HTTPResponse:
        return await self._http_client.get_async(
            url=url,
            headers=self._credentials.to_authorization_header(),
        )

    def _parse_get_response(self, response: HTTPResponse, offer_id: str) -> Offre:
        if response.status_code == http.HTTPStatus.NO_CONTENT:
            raise OffreNotFoundException(
                f"Job offer with ID '{offer_id}' not found",
                request_id=response.request_id,
            )
        return Offre.from_dict(response.body)

    def _build_search_url(self, params: dict[str, str | int | bool]) -> str:
        return FranceTravailUrl(
            JOB_OFFER_SEARCH_API_URL,
            special_mappings=self._get_special_param_mappings(),
        ).build(**params)

    def _execute_search_request(self, url: str) -> dict:
        response = self._http_client.get(
            url=url,
            headers=self._credentials.to_authorization_header(),
        )
        return response.body

    async def _execute_search_request_async(self, url: str) -> dict:
        response = await self._http_client.get_async(
            url=url,
            headers=self._credentials.to_authorization_header(),
        )
        return response.body

    def _convert_enums_to_api_values(self, params: dict) -> dict:
        return {key: self._to_api_value(value) for key, value in params.items()}

    def _to_api_value(self, value: object) -> str | int | bool | None:
        try:
            return value.to_api_value() if value is not None else None  # type: ignore[attr-defined]
        except AttributeError:
            return value  # type: ignore[return-value]

    def _get_special_param_mappings(self) -> dict[str, str]:
        return {
            "code_rome": "codeROME",
            "code_naf": "codeNAF",
            "offres_mrs": "offresMRS",
            "range_param": "range",  # 'range' is a Python reserved keyword
        }
