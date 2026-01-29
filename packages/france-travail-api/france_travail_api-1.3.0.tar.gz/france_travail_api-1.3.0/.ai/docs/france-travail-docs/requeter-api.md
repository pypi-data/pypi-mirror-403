## Requêter une API

L'URL permettant de requêter une API est constituée des éléments suivants :

  1. Le point d'accès `https://api.francetravail.io/partenaire`
  2. L'identifiant de l'API (code et version de l'API)
  3. Le nom de la ressource
  4. Les paramètres spécifiques à l'API manipulée

  
Ainsi, une requête se présente sous la forme suivante :

    
    
    https://api.francetravail.io/partenaire/[Code de l'API]/[Version de l'API]/[Nom de la ressource][Paramètres spécifiques à l'API]

  
L'en-tête HTTP suivant doit être valorisé systématiquement :

En-tête(s)| Valeur  
---|---  
Authorization| `Bearer` Valeur de l'access token  
  


#### Exemple d'appel

    
    
    GET /partenaire/labonneboite/v1/company/?distance=30&amp;latitude=49.119146&amp;rome_codes=M1607
    Authorization: Bearer [Access token]



#### Exemple de retour

    
    
    HTTP 200 OK
    Content-Type: application/json;charset=UTF-8
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "companies": [{
          "distance": 2,
          "headcount_text": "6 à 9 salariés",
          "lat": 48.97609,
          "city": "PAGNY-SUR-MOSELLE",
          "naf": "4711D",
          "name": "LIDL",
          "naf_text": "Supermarchés",
          "lon": 5.99792,
          "siret": "34326262214546"
        },
        {
          "distance": 3,
          "headcount_text": "10 à 19 salariés",
          "lat": 48.97609,
          "city": "PAGNY-SUR-MOSELLE",
          "naf": "4711D",
          "name": "CARREFOUR CONTACT",
          "naf_text": "Supermarchés",
          "lon": 5.99792,
          "siret": "50761894000021"
        }
      ]
    }

[![Accueil francetravail.io par France Travail](/assets/logo-ftio.svg)](/)[
Nous contacter ](/contact)

Produits partagés

  * [Découvrir tous nos produits](/produits-partages/catalogue)
  * [Consulter nos cas d’usage](/produits-partages/cas-usage)
  * [Implémenter techniquement nos produits](/produits-partages/documentation)
  * [Suivre la disponibilité de nos API](/etat-sante-api)

Opportunités d'innovation

  * [Booster vos produits grâce à l'échange de données](/opportunites-innovation/booster-impact-produits-echange-donnees)
  * [Participer aux initiatives Open Source de France Travail](/opportunites-innovation/participer-initiatives-open-source)
  * [Intégrer l’intelligence artificielle à votre projet](/opportunites-innovation/intelligence-artificielle)
  * [Développer ensemble nos compétences](/opportunites-innovation/developper-competences)

Nous retrouver

  * [Mon Portail Pro](https://monportailpro.francetravail.fr/)
  * [francetravail.fr](https://www.francetravail.fr)
  * [francetravail.org](https://www.francetravail.org)

Toute l'actualité de francetravail.io dans votre boite mail !

M'inscrire à la newsletter

  * [Statistiques](/statistiques)
  * [Conditions générales d’utilisation](/cgu)
  * [Cookies](/confidentialite)
  * [Accessibilité : non conforme](/accessibilite)

