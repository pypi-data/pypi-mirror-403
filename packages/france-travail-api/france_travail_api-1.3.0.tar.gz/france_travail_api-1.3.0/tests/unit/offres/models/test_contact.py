import pytest

from france_travail_api.offres.models.contact import Contact
from tests.dsl import expect


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            {
                "nom": "Etienne Dupont",
                "coordonnees1": "12 impasse du caillou",
                "coordonnees2": "Bâtiment A",
                "coordonnees3": "2ème étage",
                "telephone": "06 12 34 56 78",
                "courriel": "Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX",
                "commentaire": "A contacter après 19h",
                "urlRecruteur": "https://boulanger-austral.net",
                "urlPostulation": "https://boulanger-austral.net/carrieres",
            },
            Contact(
                nom="Etienne Dupont",
                coordonnees1="12 impasse du caillou",
                coordonnees2="Bâtiment A",
                coordonnees3="2ème étage",
                telephone="06 12 34 56 78",
                courriel="Pour postuler, utiliser le lien suivant : https://candidat.francetravail.fr/offres/recherche/detail/XXXXXXX",
                commentaire="A contacter après 19h",
                url_recruteur="https://boulanger-austral.net",
                url_postulation="https://boulanger-austral.net/carrieres",
            ),
        ),
        (
            {},
            Contact(
                nom=None,
                coordonnees1=None,
                coordonnees2=None,
                coordonnees3=None,
                telephone=None,
                courriel=None,
                commentaire=None,
                url_recruteur=None,
                url_postulation=None,
            ),
        ),
        (
            {
                "urlRecruteur": "https://example.com",
                "urlPostulation": "https://example.com/apply",
            },
            Contact(
                nom=None,
                coordonnees1=None,
                coordonnees2=None,
                coordonnees3=None,
                telephone=None,
                courriel=None,
                commentaire=None,
                url_recruteur="https://example.com",
                url_postulation="https://example.com/apply",
            ),
        ),
    ],
)
def test_from_dict_should_create_contact(data: dict, expected: Contact) -> None:
    expect(Contact.from_dict(data)).to_equal(expected)
