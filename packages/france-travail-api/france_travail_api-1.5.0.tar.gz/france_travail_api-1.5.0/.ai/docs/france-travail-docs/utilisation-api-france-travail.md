## Utiliser les API

Pour consommer une API exposée sur francetravail.io, vous devez authentifier
votre application ou permettre l'authentification de l'utilisateur final. Les
informations ci-dessous permettent de déterminer le type d'authentification à
implémenter.

###  

### Identifier le royaume

Le paramètre `royaume` est indiqué dans la documentation technique de l'API
que vous souhaitez consommer.

![](https://francetravail.io/api-peio/v2/images/728/identifier-royaume.png)



Le tableau suivant décrit le type d'authentification à implémenter en fonction
du paramètre `royaume`.

Royaume| Type d'authentification  
---|---  
`/partenaire`| Cette authentification repose sur la cinématique [Client
credentials grant](https://auth0.com/docs/get-started/authentication-and-
authorization-flow/client-credentials-flow) du protocole OAuth 2.0. Elle
permet d'authentifier une `application`.  
`/individu`| Cette authentification repose sur la cinématique [Authorization
code flow](https://auth0.com/docs/get-started/authentication-and-
authorization-flow/authorization-code-flow) du protocole OAuth 2.0 et basée
sur le standard OpenID Connect.  Elle permet d'authentifier des `demandeurs
d'emploi`.  
`/entreprise`| Cette authentification repose sur la cinématique [Authorization
code flow](https://auth0.com/docs/get-started/authentication-and-
authorization-flow/authorization-code-flow)  du protocole OAuth 2.0 et basée
sur le standard OpenID Connect.  Elle permet d'authentifier des `employeurs`.  
`/agent`| Cette authentification repose sur la cinématique [Authorization code
flow](https://auth0.com/docs/get-started/authentication-and-authorization-
flow/authorization-code-flow)  du protocole OAuth 2.0 et basée sur le standard
OpenID Connect. Elle permet d'authentifier des `agents du réseau France
Travail`.  
  


### Identifier la cinématique d'authentification à implémenter (avec ou sans
PKCE)

**Afin de garantir la sécurité des données, vous devez identifier le niveau de
sécurité de l'application sur laquelle vous implémentez l'authentification.**

Votre service d'authentification est réalisé sur une `application privée`
(exemple : application hébergée sur un serveur). Ce service permet la
confidentialité des identifiants. La cinématique [Authorization
Code](https://francetravail.io/produits-partages/documentation/utilisation-
api-france-travail/authorization-code-flow) est suffisante.

Votre service d'authentification est réalisé sur une `application publique`
(exemple : application web fonctionnant dans le navigateur). Ce service ne
permet pas la confidentialité des identifiants. Vous devez renforcer la
sécurité de votre service en utilisant la cinématique [Authorization code with
PKCE](https://francetravail.io/produits-partages/documentation/utilisation-
api-france-travail/authorization-code-with-pkce).



### En résumé

**Vous authentifiez**| **Application**| **Cinématique d'authentification**|
**URI d'authentification**| **URI de forge d'un token**  
---|---|---|---|---  
Une application| Privée| [Client
credentials](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/client-credentials)| Pas
d'authentification utilisateur|

    
    
    POST https://francetravail.io/connexion/oauth2/access_token  
  
Un demandeur d'emploi| Privée| [Authorization
code](https://francetravail.io/produits-partages/documentation/utilisation-
api-france-travail/authorization-code-flow)|

    
    
    GET https://authentification-candidat.francetravail.fr/connexion/oauth2/authorize

|

    
    
    POST https://authentification-candidat.francetravail.fr/connexion/oauth2/access_token  
  
Publique| [Authorization code with PKCE](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/authorization-code-with-
pkce)  
Un employeur| Privée| [Authorization code](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/authorization-code-
flow)|

    
    
    GET https://entreprise.francetravail.fr/connexion/oauth2/authorize

|

    
    
    POST https://entreprise.francetravail.fr/connexion/oauth2/access_token  
  
Publique| [Authorization code with PKCE](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/authorization-code-with-
pkce)  
Un agent| Privée| [Authorization code](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/authorization-code-
flow)|

    
    
    GET https://proxyproconnect.francetravail.net/connexion/oauth2/agent/authorize

|

    
    
    POST https://proxyproconnect.francetravail.net/connexion/oauth2/acces_token  
  
Publique| [Authorization code with PKCE](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/authorization-code-with-
pkce)  
  


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

