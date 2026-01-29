from typing import Any, cast

from france_travail_api.auth._credentials import FranceTravailCredentials
from france_travail_api.http_transport._http_client import HttpClient
from france_travail_api.http_transport._http_response import HTTPResponse
from france_travail_api.offres.models.metier import Metier

REFERENTIEL_METIERS_API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/metiers"


class ReferentielsClient:
    def __init__(self, credentials: FranceTravailCredentials, http_client: HttpClient) -> None:
        self._credentials = credentials
        self._http_client = http_client

    def metiers(self) -> list[Metier]:
        """Get the ROME jobs (métiers) referential.

        Returns
        -------
        list[Metier]
            List of ROME jobs with their codes and labels

        Examples
        --------
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> client.referentiels.metiers()
        [Metier(code="D1102", libelle="Boulangerie - viennoiserie"), ...]

        References
        ----------
        .. [1] France Travail API Documentation - Référentiel - Métiers ROME
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererReferentielMetiers
        """
        response = self._execute_get_request(REFERENTIEL_METIERS_API_URL)
        return self._parse_metiers_response(response)

    async def metiers_async(self) -> list[Metier]:
        """Get the ROME jobs (métiers) referential asynchronously.

        Returns
        -------
        list[Metier]
            List of ROME jobs with their codes and labels

        Examples
        --------
        >>> import asyncio
        >>> client = FranceTravailOffresClient(credentials, http_client)
        >>> asyncio.run(client.referentiels.metiers_async())
        [Metier(code="D1102", libelle="Boulangerie - viennoiserie"), ...]

        References
        ----------
        .. [1] France Travail API Documentation - Référentiel - Métiers ROME
           https://francetravail.io/produits-partages/catalogue/offres-emploi/documentation#/api-reference/operations/recupererReferentielMetiers
        """
        response = await self._execute_get_request_async(REFERENTIEL_METIERS_API_URL)
        return self._parse_metiers_response(response)

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

    def _parse_metiers_response(self, response: HTTPResponse) -> list[Metier]:
        metiers_data = cast(list[dict[str, Any]], response.body)
        return [Metier.from_dict(metier_json) for metier_json in metiers_data]
