## Erreurs fréquentes

### 302 Found

#### Identifiant client erroné ou absent

    
    
    HTTP 302 Moved Permanently
    [URL de redirection]?error=invalid_client
    error_description=Client%20authentication%20failed
    state=[state]

####  
Scope inconnu ou scope pour lequel vous ne disposez pas des droits
(utilisation d'une API en accès libre)

    
    
    HTTP 302 Moved Permanently
    [URL de redirection]?error=invalid_scope
    error_description=Unknown%2Finvalid%20scope%28s%29%3A%20%5Bapi_labonneboitev1%2C%20api_infotravailv1
    state=[state]

####  
Mauvaise cinématique OAuth

    
    
    HTTP 302 Moved Permanently
    [URL de redirection]?error=unsupported_response_type
    error_description=Unsupported%20response_type%20value
    state=[state]

####  
L'utilisateur annule sa demande d'authentification

    
    
    HTTP 302 Moved Permanently
    [URL de redirection]?state=[state]

####  
L'utilisateur ne valide pas les consentements liés aux scopes demandés

    
    
    HTTP 302 Moved Permanently
    [URL de redirection]?error=access_denied
    error_description=Resource%20Owner%20did%20not%20authorize%20the%20request
    state=[state]

###  

### 400 Bad Request

#### Identifiant client et/ou clé secrète erroné ou absent

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "invalid_client",
      "error_description": "Client authentication failed"
    }

####  

#### Scope inconnu ou pour lequel vous ne disposez pas des droits (utilisation
d'une API en accès libre)

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "invalid_scope",
      "error_description": "Unknown/invalid scope(s): [api_quinexistepasv0]"
    }

####  

#### Mauvaise cinématique OAuth

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "unsupported_grant_type",
      "error_description": "Grant type is not supported: implicit_grant"
    }



#### Mauvaise cinématique Oauth

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "invalid_grant",
      "error_description": "The provided access grant is invalid, expired, or revoked."
    }

####  

#### URI de redirection erronée ou absente

    
    
    HTTP 400 Bad Request
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache
    
    
    {
      "error": "redirect_uri_mismatch",
      "error_description": "The redirection URI provided does not match a pre-registered value."
    }

###  

### 401 Unauthorized

#### Access token érroné ou absent de la requête

    
    
    HTTP 401 Unauthorized
    Content-Type: application/json
    Cache-Control: no-store
    Pragma: no-cache



### 429 Too Many Requests

#### Dépassement de quota

    
    
    HTTP 429 Too Many Requests
    Content-Type: text/plain
    Retry-After: [Nombre de secondes à attendre avant de réémettre la requête]
    Cache-Control: no-store
    Pragma: no-cache

Vous disposez également des headers suivants :

X-Ratelimit-Burst-Capacity-Clientidlimiter : ce header correspond aux nombres
d'appels maximum par seconde autorisés par API pour votre application

X-Ratelimit-Remaining-Clientidlimiter : ce header correspond aux nombres
d'appels restants sur une seconde pour l'API pour votre application

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

