from france_travail_api._url import FranceTravailUrl
from tests.dsl import expect


def test_should_convert_snake_case_to_camel_case() -> None:
    url = FranceTravailUrl("https://api.example.com").build(
        mots_cles="test",
        code_rome="M1805",
        secteur_activite="62",
        acces_travailleur_handicape=True,
    )

    expect(url).to_contain("motsCles=test")
    expect(url).to_contain("codeRome=M1805")
    expect(url).to_contain("secteurActivite=62")
    expect(url).to_contain("accesTravailleurHandicape=true")


def test_should_handle_single_word_parameters() -> None:
    url = FranceTravailUrl("https://api.example.com").build(sort=1, domaine="M18")

    expect(url).to_contain("sort=1")
    expect(url).to_contain("domaine=M18")


def test_should_transform_boolean_to_lowercase_string() -> None:
    url = FranceTravailUrl("https://api.example.com").build(
        temps_plein=True,
        inclure_limitrophes=False,
        accessible=True,
    )

    expect(url).to_contain("tempsPlein=true")
    expect(url).to_contain("inclureLimitrophes=false")
    expect(url).to_contain("accessible=true")


def test_should_transform_integers_to_string() -> None:
    url = FranceTravailUrl("https://api.example.com").build(
        origine_offre=1,
        distance=10,
        publiee_depuis=7,
        count=0,
    )

    expect(url).to_contain("origineOffre=1")
    expect(url).to_contain("distance=10")
    expect(url).to_contain("publieeDepuis=7")
    expect(url).to_contain("count=0")


def test_should_keep_strings_unchanged() -> None:
    url = FranceTravailUrl("https://api.example.com").build(
        type_contrat="CDI",
        qualification="cadre",
        code="ABC123",
    )

    expect(url).to_contain("typeContrat=CDI")
    expect(url).to_contain("qualification=cadre")
    expect(url).to_contain("code=ABC123")


def test_should_handle_special_mappings() -> None:
    url = FranceTravailUrl(
        "https://api.example.com",
        special_mappings={
            "code_rome": "codeROME",
            "code_naf": "codeNAF",
            "range_param": "range",
        },
    ).build(
        code_rome="M1805",
        code_naf="62.02A",
        range_param="0-149",
        mots_cles="test",
    )

    expect(url).to_contain("codeROME=M1805")
    expect(url).to_contain("codeNAF=62.02A")
    expect(url).to_contain("range=0-149")
    expect(url).to_contain("motsCles=test")


def test_should_build_url_with_only_required_parameter() -> None:
    url = FranceTravailUrl("https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search").build(
        mots_cles="développeur python"
    )

    expect(url).to_equal(
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search?motsCles=développeur python"
    )


def test_should_ignore_none_parameters() -> None:
    url = FranceTravailUrl("https://api.example.com").build(
        mots_cles="développeur",
        sort=None,
        domaine="M18",
        commune=None,
    )

    expect(url).to_contain("motsCles=développeur")
    expect(url).to_contain("domaine=M18")
    expect(url).to_not_contain("sort")
    expect(url).to_not_contain("commune")


def test_should_build_url_with_france_travail_special_mappings() -> None:
    url = FranceTravailUrl(
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
        special_mappings={
            "code_rome": "codeROME",
            "code_naf": "codeNAF",
            "offres_mrs": "offresMRS",
        },
    ).build(
        mots_cles="développeur python",
        code_rome="M1805,M1810",
        code_naf="62.02A",
        offres_mrs=True,
    )

    expect(url).to_contain("motsCles=développeur python")
    expect(url).to_contain("codeROME=M1805,M1810")
    expect(url).to_contain("codeNAF=62.02A")
    expect(url).to_contain("offresMRS=true")


def test_should_handle_all_parameter_types_together() -> None:
    url = FranceTravailUrl("https://api.example.com/search").build(
        mots_cles="développeur python",
        sort=1,
        commune="75056",
        distance=10,
        temps_plein=True,
        type_contrat="CDI",
    )

    expect(url).to_contain("motsCles=développeur python")
    expect(url).to_contain("sort=1")
    expect(url).to_contain("commune=75056")
    expect(url).to_contain("distance=10")
    expect(url).to_contain("tempsPlein=true")
    expect(url).to_contain("typeContrat=CDI")


def test_should_accept_custom_base_url() -> None:
    url = FranceTravailUrl("https://custom-api.example.com/v3/search").build(mots_cles="test", sort=1)

    expect(url).to_start_with("https://custom-api.example.com/v3/search?")
    expect(url).to_contain("motsCles=test")
    expect(url).to_contain("sort=1")


def test_should_work_with_completely_different_api() -> None:
    url = FranceTravailUrl(
        "https://api.example.com/search",
        special_mappings={
            "query": "q",
            "max_results": "limit",
        },
    ).build(
        query="python",
        max_results=10,
        user_name="john",
    )

    expect(url).to_contain("q=python")
    expect(url).to_contain("limit=10")
    expect(url).to_contain("userName=john")
    expect(url).to_not_contain("maxResults")
