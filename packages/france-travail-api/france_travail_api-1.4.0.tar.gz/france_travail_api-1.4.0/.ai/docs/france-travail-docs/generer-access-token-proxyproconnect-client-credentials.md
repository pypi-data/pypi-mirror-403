## Générer un access token Proxyproconnect (Client Credentials)

### Description de la requête

#### Point d'accès

    
    
    POST https://proxyproconnect.francetravail.net/connexion/oauth2/access_token

####  

#### Détail des paramètres à valoriser

Paramètre(s)| Valeur  
---|---  
realm| `/agent`  
  


En-tête(s)| Valeur  
---|---  
Content-Type| `application/x-www-form-urlencoded`  
  


Corps de la requête| Valeur  
---|---  
grant_type| `client_credentials`  
client_id| Votre identifiant client  
client_secret| Votre clé secrète  
scope| Liste des scopes techniques et applicatifs correspondant aux API que
vous souhaitez manipuler (séparés par des espaces). La documentation de chaque
API contient des informations détaillées sur chaque scope à implémenter.  
  


#### Exemple d'appel

    
    
    POST /connexion/oauth2/access_token?realm=%2Fagent
    Content-Type: application/x-www-form-urlencoded
    
    grant_type=client_credentials
    &client_id=[identifiant client]
    &client_secret=[clé secrète]
    &scope=api_rendez-vous-partenairev1 gererRDV

###  

### Description de la réponse

En-tête(s)| Valeur  
---|---  
Content-Type| `application/json;charset=UTF-8`  
Cache-Control| `no-store`  
Pragma| `no-cache`  
  


Corps de la réponse| Valeur  
---|---  
expires_in| Durée de vie de l'access token en secondes  
token_type| `Bearer`  
access_token| Valeur de l'access token généré  
scope| Liste des scopes techniques et applicatifs demandés  
  


#### Exemple de retour

    
    
    HTTP 200 OK
    Content-Type: application/json;charset=UTF-8
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "scope": "api_rechercher-usagerv2 rechercherusager",
      "expires_in": 1499,
      "token_type": "Bearer",
      "access_token": "[Valeur du jeton généré]"
    }



### Cas d'erreurs possibles

#### Identifiant client et/ou clé secrète erroné ou absent

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "invalid_client",
      "error_description": "Client authentication failed"
    }



#### Scope inconnu ou scope pour lequel vous ne disposez pas des droits
(utilisation d'une API en accès libre)

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "invalid_scope",
      "error_description": "Unknown/invalid scope(s): [api_rechercher-usagerv2]"
    }



#### Mauvaise cinématique OAuth

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "unsupported_grant_type",
      "error_description": "Grant type is not supported: authorization_code_flow"
    }



[Voir les cas d'erreurs fréquents](produits-partages/documentation/erreurs-
frequentes)

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

