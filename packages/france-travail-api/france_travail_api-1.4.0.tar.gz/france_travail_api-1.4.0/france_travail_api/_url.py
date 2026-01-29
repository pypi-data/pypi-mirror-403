from typing import Any


class FranceTravailUrl:
    """Extensible factory for building URLs with query parameters using conventions for France Travail API.

    This class eliminates hardcoded parameter mappings by using conventions:
    - Parameter names: snake_case → camelCase
    - Values: bool → "true"/"false", int/str → str

    The base URL is configurable via constructor for maximum extensibility.

    Parameters
    ----------
    base_url : str
        The base URL to which query parameters will be appended
    special_mappings : dict[str, str], optional
        Override default camelCase conversion for specific parameters.
        Example: {"code_rome": "codeROME", "range_param": "range"}

    Examples
    --------
    >>> # France Travail API with special mappings
    >>> url = FranceTravailUrl(
    ...     "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
    ...     special_mappings={"code_rome": "codeROME", "code_naf": "codeNAF", "range_param": "range"}
    ... )
    >>> url.build(mots_cles="python", code_rome="M1805", temps_plein=True)
    'https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search?motsCles=python&codeROME=M1805&tempsPlein=true'
    """

    def __init__(
        self,
        base_url: str,
        special_mappings: dict[str, str] | None = None,
    ) -> None:
        """Initialize the URL builder with a base URL and optional special mappings.

        Parameters
        ----------
        base_url : str
            The base URL to which query parameters will be appended
        special_mappings : dict[str, str], optional
            Override default camelCase conversion for specific parameters.
        """
        self.base_url = base_url
        self._special_mappings = special_mappings or {}

    def build(self, **kwargs: Any) -> str:
        """Build the complete URL with query parameters using conventions.

        Parameters are automatically converted:
        - Names: snake_case → camelCase (with special_mappings overrides)
        - Values: bool → "true"/"false", int → str, str → unchanged

        Parameters
        ----------
        **kwargs : Any
            Search parameters in snake_case format

        Returns
        -------
        str
            Complete URL with query parameters

        Examples
        --------
        >>> url = FranceTravailUrl("https://api.example.com/search")
        >>> url.build(mots_cles="développeur", commune="75056", temps_plein=True)
        'https://api.example.com/search?motsCles=développeur&commune=75056&tempsPlein=true'
        """
        params: dict[str, str] = {}

        for python_name, value in kwargs.items():
            if value is not None:
                api_name = self._get_api_name(python_name)
                params[api_name] = self._transform_value(value)

        query_string = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{self.base_url}?{query_string}"

    @staticmethod
    def _to_camel_case(snake_case_string: str) -> str:
        """Convert snake_case to camelCase.

        Examples
        --------
        >>> FranceTravailUrl._to_camel_case("mots_cles")
        'motsCles'
        >>> FranceTravailUrl._to_camel_case("acces_travailleur_handicape")
        'accesTravailleurHandicape'
        """
        components = snake_case_string.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    @staticmethod
    def _transform_value(value: Any) -> str:
        """Transform a value according to conventions.

        - bool → "true"/"false" (lowercase)
        - int → string representation
        - str → unchanged

        Examples
        --------
        >>> FranceTravailUrl._transform_value(True)
        'true'
        >>> FranceTravailUrl._transform_value(42)
        '42'
        >>> FranceTravailUrl._transform_value("CDI")
        'CDI'
        """
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)

    def _get_api_name(self, python_name: str) -> str:
        """Get the API parameter name for a Python parameter name.

        Uses special_mappings if available, otherwise applies camelCase convention.

        Examples
        --------
        >>> url = FranceTravailUrl("https://api.example.com", {"code_rome": "codeROME"})
        >>> url._get_api_name("code_rome")
        'codeROME'
        >>> url._get_api_name("mots_cles")
        'motsCles'
        """
        return self._special_mappings.get(python_name, self._to_camel_case(python_name))
