## Utiliser le mode bac à sable d'une API

Le mode bac à sable d'une API permet de faire des appels en mode bouchonné.

Pour cela, il est nécessaire de [générer un acces token](produits-
partages/documentation/utilisation-api-france-travail/generer-access-token) en
passant en paramètre le(s) scope(s) de l'API. (voir la Documentation de l'API)

Il est nécessaire de modifier le scope de l'API en ajoutant **test**. Ex :
api_**test** diagnosticargumentev3



#### Exemple d'appel

    
    
    POST /connexion/oauth2/access_token?realm=%2Fpartenaire
    Content-Type: application/x-www-form-urlencoded
    
    grant_type=client_credentials
    &client_id=[identifiant client]
    &client_secret=[clé secrète]
    &scope=api_testdiagnosticargumentev3

###  

L'URL permettant de requêter une API en mode bac à sable est constituée des
éléments suivants :

  1. Le point d'accès `https://api.francetravail.io/partenaire`
  2. L'identifiant de l'API (code et version de l'API) précédée de **test**
  3. Le nom de la ressource
  4. Les paramètres spécifiques à l'API manipulée

  
Ainsi, une requête se présente sous la forme suivante :

    
    
    https://api.francetravail.io/partenaire/test[Code de l'API]/[Version de l'API]/[Nom de la ressource][Paramètres spécifiques à l'API]

  
L'en-tête HTTP suivant doit être valorisé systématiquement :

En-tête(s)| Valeur  
---|---  
Authorization| `Bearer` Valeur de l'access token  
  


#### Exemple d'appel

    
    
    GET /partenaire/testdiagnosticargumente/v3/individus/52c4159a-4d11-4c41-a248-a23651c4fde16e8%23VMlG-rXWsKF0mp8PZgYJqtbDVbv_csN0Kxmps85MlNA/diagnostics
    Authorization: Bearer [Access token]



#### Exemple de retour

    
    
    HTTP 204 No Content
    Content-Type: application/json;charset=UTF-8
    Cache-Control: no-store
    Pragma: no-cache

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

