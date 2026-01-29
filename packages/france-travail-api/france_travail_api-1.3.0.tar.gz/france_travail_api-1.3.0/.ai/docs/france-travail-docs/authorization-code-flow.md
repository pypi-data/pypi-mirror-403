## Authorization code Flow

La cinématique `Authorization code Flow` permet d'authentifier les
utilisateurs de votre application (demandeurs d'emploi, candidats,
entreprises, recruteurs ou agents France Travail).

Si le niveau de sécurité de votre application ne permet pas de sécuriser le
stockage de vos identifiants, vous devez renforcer la sécurité de votre
service en utilisant la cinématique [_Authorization code with
PKCE_](https://francetravail.io/produits-partages/documentation/utilisation-
api-france-travail/authorization-code-with-pkce).

#### Illustration de la cinématique

![](https://francetravail.io/api-peio/v2/images/1058/Authorization code Flow
FT.io.png)

#### Détail des étapes

  1. L'application envoie une demande d'autorisation + les paramètres `state` et `nonce`
  2. L'utilisateur est redirigé vers le serveur d'autorisation et donne son consentement
  3. L'application reçoit un code d'autorisation + le paramètre `state`
  4. Vous devez valider la valeur du `state` puis transférer le code d'autorisation vers la partie serveur de votre application
  5. L'application envoie une demande pour récupérer un `access token`
  6. Le serveur France Travail vous envoie un `access token`
  7. Vous devez valider la valeur du `nonce`, l'`access token` et l'`id token` reçus en retour

###  

### Authentifier un utilisateur

Ce point d'accès est appelé depuis la partie cliente de votre application. Il
vous permet d'authentifier un utilisateur auprès de France Travail.

#### Point d'accès

Population d'utilisateurs| URL| Royaume  
---|---|---  
Demandeurs d'emploi et candidats (**Dispositif France Travail Connect**)|

    
    
    GET https://authentification-candidat.francetravail.fr/connexion/oauth2/authorize

| /individu  
Entreprises et recruteurs (**Dispositif France Travail Connect**)|

    
    
    GET https://entreprise.francetravail.fr/connexion/oauth2/authorize

| /employeur  
Agents|

    
    
    GET https://proxyproconnect.francetravail.net/connexion/oauth2/agent/authorize

| /agent  
  


Pour les API du dispositif France Travail Connect, vous devez intégrer ce
point d'accès à partir du [bouton de
connexion](https://francetravail.io/produits-partages/documentation/5-savoir-
dispositif-france-travail-connect/maquettes-charte) fourni par France Travail.

L'utilisateur accède aux écrans suivants :

  * écran de connexion → l'utilisateur saisit ses identifiants France Travail
  * écran de consentement (**pour les API du Dispositif France Connect uniquement**) → l'utilisateur autorise votre application à accéder à ses données personnelles

Suite à l'authentification et au consentement de l'utilisateur, le serveur
d'authentification réalise une redirection vers la `redirect_uri` indiquée et
votre application obtient en retour un `authorization code` (l'utilisation du
_localhost_ n'est pas possible).

Remarques :

  * Si vous souhaitez rediriger l'utilisateur vers la page consultée avant son authentification, vous devez enregistrer cette dernière dans la session de l'utilisateur ou dans un cookie.
  * Vous pouvez demander des scopes complémentaires au cours de la session de l'utilisateur. Pour cela, vous devez reprendre l'ensemble de la cinématique en ajoutant les nouveaux scopes. Le serveur d'authentification affichera la page de consentement complétée des nouveaux scopes demandés.
  * L'écran de consentement n'existe pas dans le parcours propre aux agents.

####  
Détail des paramètres à valoriser

Paramètre(s)| Valeur  
---|---  
realm (**uniquement pour les API France Connect**)| `/individu` ou
`/employeur`  
response_type| `code`  
client_id| Votre identifiant client  
scope| Liste des scopes techniques et applicatifs correspondant aux API que
vous souhaitez manipuler (séparés par des espaces et encodés au format URL)  
redirect_uri| Liens de redirection définie dans les paramètres de votre
application dans francetravail.io (encodée au format URL). Seul le port 80
peut être utilisé. (L'utilisation du LOCALHOST n'est pas possible.)  
state| Hash unique d’un nombre aléatoire généré par votre application et
stocké dans la session de l’utilisateur (paramètre anti-faille CSRF)  
nonce| Hash unique d’un nombre aléatoire généré par votre application et
stocké dans la session de l’utilisateur (paramètre anti-faille CSRF)  
  


#### Exemple d'appel

    
    
    GET /connexion/oauth2/authorize?realm=%2Findividu
    Host : authentification-candidat.francetravail.fr
    
    response_type=code
    client_id=[identifiant client]
    scope=api_peconnect-individuv1%20openid%20profile%20email
    redirect_uri=[URL de redirection]
    state=[state]
    nonce=[nonce]

####  
Description de la redirection

Paramètre(s)| Valeur  
---|---  
code| Valeur de l'authorization code généré  
iss| URL du serveur d'authentification  
client_id| Votre identifiant client  
state| Identique à celui fourni lors de l'appel  
  


Afin de s'assurer de la provenance des échanges (anti-faille CSRF), votre
application doit vérifier que le paramètre `state` __ reçu est identique à
celui généré préalablement par votre application.

####  

#### Exemple de retour

    
    
    HTTP 302 Found
    
    Location:
    [URI de redirection]?code=[valeur de l'authorization code généré]
    scope=api_rechercher-usagerv2%20rechercheusager%20profil_accedant
    iss=[URL du serveur d'authentification]
    client_id=[identifiant client]
    state=[state]

Au retour du endpoint, la page indiquée dans le paramètre `redirect_uri` est
affichée.

Vous pouvez réaliser une redirection vers la page initiale de l'utilisateur
sauvegardée préalablement dans sa session ou dans un cookie.  
Vous devez valider la valeur du `state` reçu en retour et transférer
l'`Authorization code` de votre application cliente vers votre serveur
d'application.



### Générer un access token

Ce point d'accès est appelé depuis la partie serveur de votre application.

#### Point d'accès

Population d'utilisateurs| URL| Royaume  
---|---|---  
Demandeurs d'emploi et candidats|

    
    
    POST https://authentification-candidat.francetravail.fr/connexion/oauth2/access_token

| /individu  
Entreprises et recruteurs|

    
    
    POST https://entreprise.francetravail.fr/connexion/oauth2/access_token

| /employeur  
Agents|

    
    
    POST https://proxyproconnect.francetravail.net/connexion/oauth2/access_token

| /agent  
  


Ce point d'accès permet à votre application d'échanger un `authorization code`
__ contre un `access token`. Ce dernier est utilisé pour tous les échanges
entre votre application et l'API afin d'accéder aux données.

Remarques :

  * Afin de s'assurer de la provenance des échanges (anti-faille CSRF), votre application doit vérifier que le paramètre `nonce` reçu est identique à celui généré préalablement par votre application lors de l'appel au point d'accès d'authentification.
  * Vous devez également valider la valeur de l’`access token` et de l’`id token` selon les principes OpenID Connect pour s’assurer que l’émetteur est bien France Travail et que son contenu n’a pas été altéré pendant le transport.

####  

#### Détail des paramètres à valoriser

Paramètre(s)| Valeur  
---|---  
realm| `/individu` ou `/employeur` ou `/agent`Attention, le _realm_ doit être
passé en paramètre, et non dans le body.  
  


En-tête(s)| Valeur  
---|---  
Content-Type| `application/x-www-form-urlencoded`  
  


Corps de la requête| Valeur  
---|---  
grant_type| `authorization_code`  
code| Valeur de l'authorization code  
client_id| Votre identifiant client  
client_secret| Votre clé secrète  
redirect_uri| URL de redirection passée lors de la demande d'authentification
de l'utilisateur (étape 1)  
  
####  
Exemple d'appel

    
    
    POST /connexion/oauth2/access_token?realm=%2Findividu
    Content-Type: application/x-www-form-urlencoded
    Host : authentification-candidat.francetravail.fr
    
    grant_type=authorization_code
    &code=[authorization code]
    &client_id=[identifiant client]
    &client_secret=[clé secrète]
    &redirect_uri=[URL de redirection]

####  
Description de la réponse

En-tête(s)| Valeur  
---|---  
Content-Type| `application/json;charset=UTF-8`  
Cache-Control| `no-store`  
Pragma| `no-cache`  
  


Corps de la réponse| Valeur  
---|---  
scope| Liste des scopes techniques et applicatifs demandés  
expires_in| Durée de vie de l'access token (en seconde)  
token_type| `Bearer`  
access_token| Valeur de l'access token généré  
id_token| Valeur de l'id token généré  
(requis pour [déconnecter l'utilisateur](https://francetravail.io/produits-
partages/documentation/utilisation-api-france-travail/deconnexion-
utilisateur))  
refresh_token| Ce jeton n'est pas utilisé par la cinématique proposée par
France Travail  
nonce| Identique à celui fourni lors de l'appel du point d'accès
d'authentification  
  
####  


#### Exemple de retour

    
    
    HTTP 200 OK
    
    {
      "scope": "api_peconnect-individuv1 openid profile email",
      "expires_in": 59,
      "token_type": "Bearer",
      "access_token": "[valeur de l'access token généré]",
      "id_token": "[valeur de l'id token généré]",
      "refresh_token": "[valeur du refresh token généré]",
      "nonce": "[nonce]"
    }

Vous devez valider la valeur du `nonce`, l'`access token` et l'`id token`
reçus en retour.



### Et maintenant ?

  * Découvrir comment [requêter une API](https://francetravail.io/produits-partages/documentation/utilisation-api-france-travail/requeter-api)
  * Passer à l'étape de [déconnexion de votre utilisateur](https://francetravail.io/produits-partages/documentation/utilisation-api-france-travail/deconnexion-utilisateur)
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

