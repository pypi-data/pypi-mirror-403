## Client Credentials Flow

La cinématique Client credentials grant est utilisée pour authentifier votre
application afin d'échanger des données de serveur à serveur.

![](https://francetravail.io/api-peio/v2/images/1062/Client Credentials Flow
FT.io.png)

### Générer un access token

Ce point d'accès est appelé depuis la partie serveur de votre application.

####  

#### Point d'accès

    
    
    POST https://entreprise.francetravail.fr/connexion/oauth2/access_token

Il permet à votre application d'obtenir un `access token` à partir d'un
`identifiant client`, d'un `secret client` et de `scopes`. Les scopes que vous
échangez sont contrôlés et définissent le périmètre de données auquel vous
avez accès.

####  

#### Détail des paramètres à valoriser

Paramètre(s)| Valeur  
---|---  
realm| `/partenaire`  
  


En-tête(s)| Valeur  
---|---  
Content-Type| `application/x-www-form-urlencoded`  
  


Corps de la requête| Valeur  
---|---  
grant_type| `client_credentials`  
client_id| Votre identifiant client  
client_secret| Votre clé secrète  
scope| Liste des scopes techniques et applicatifs correspondant aux API que
vous souhaitez manipuler (séparés par des espaces)  
  


#### Exemple d'appel

    
    
    POST /connexion/oauth2/access_token?realm=%2Fpartenaire
    Content-Type: application/x-www-form-urlencoded
    Host: francetravail.io
    
    grant_type=client_credentials
    &client_id=[identifiant client]
    &client_secret=[clé secrète]
    &scope=api_offresdemploiv2 o2dsoffre

###  

### Description de la réponse

Corps de la réponse| Valeur  
---|---  
expires_in| Durée de vie de l'access token en secondes  
token_type| `Bearer`  
access_token| Valeur de l'access token généré  
scope| Liste des scopes techniques et applicatifs demandés  
  


#### Exemple de retour

    
    
    HTTP 200 OK
    
    {
      "scope": "api_offresdemploiv2 o2dsoffre",
      "expires_in": 1499,
      "token_type": "Bearer",
      "access_token": "[Valeur du jeton généré]"
    }



### Et maintenant ?

  * Découvrir comment [requêter une API](https://francetravail.io/produits-partages/documentation/utilisation-api-france-travail/requeter-api)
  * Consulter les [cas d'erreurs fréquents](https://francetravail.io/produits-partages/documentation/erreurs-frequentes)

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

