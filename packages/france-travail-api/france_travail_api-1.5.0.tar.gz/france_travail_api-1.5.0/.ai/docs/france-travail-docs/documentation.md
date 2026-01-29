
###  Pré-requis

Pour utiliser une API, vous devez au préalable avoir :

  * déclaré une application,
  * souscrit à une API afin d'obtenir un identifiant client et une clé secrète.

### Identifiants

Un identifiant client et une clé secrète vous sont délivrés par application
lorsque vous souscrivez à une première API.

Conservez précieusement ces informations nécessaires pour requêter les API.
Vous les retrouverez à tout moment sur la page de configuration de votre
application accessible depuis votre espace.

Veillez à protéger votre identifiant client et clé secrète en suivant ces
bonnes pratiques :

  * Ne faites pas figurer vos identifiants en clair dans le code source de votre application mais enregistrez-les dans des variables d'environnement ou dans des fichiers dédiés protégés
  * Retirez ceux devenus inutiles et informez le support qui les supprimera
  * Lorsque vous publiez du code sur une plateforme de gestion de versions, assurez-vous que vos identifiants n'apparaissent pas
  * La clé secrète doit être uniquement présente sur la partie serveur de votre application

###  
Protocoles et standards

  * Les API exposées respectent les contraintes de l'architecture REST
  * Les API sont sécurisées via le protocole [OAuth 2.0](http://oauth.net/2/) et respectent le standard [OpenID Connect](http://openid.net/connect/)
  * OAuth 2.0 et OpenID Connect imposent l'utilisation de HTTPS (TLS V1.2 minimum) pour tous les échanges effectués compte tenu de la sensibilité des données qui transitent
  * Les ressources sont distribuées au format JSON

###  
Serveur d'authentification France Travail

Il s'agit d'un dispositif d'autorisation fabriqué par France Travail basé sur
le protocole OAuth 2.0 et intégrant le standard OpenID Connect. Il apporte les
fonctionnalités suivantes :

  * la délégation de l'authentification des utilisateurs de votre application avec leur compte France Travail,
  * un mécanisme d'authentification unique sur l'ensemble des services France Travail,
  * un moyen d'obtenir des informations sur l'utilisateur connecté à votre application (via consentement).

La solution se décline en trois royaumes, chacun adressant une population
d'utilisateurs :

Population d'utilisateurs| URL| Royaume  
---|---|---  
Demandeurs d'emploi et candidats|

    
    
    https://authentification-candidat.francetravail.fr

| `/individu`  
Entreprises et recruteurs|

    
    
    https://entreprise.francetravail.fr

| `/employeur`  
Partenaires|

    
    
    https://entreprise.francetravail.fr

| `/partenaire`  
  


### Cinématiques OAuth

La cinématique OAuth à implémenter dépend de votre besoin d'authentifier ou
non l'utilisateur final de votre application avec son compte France Travail :

  * sans authentification de l'utilisateur, implémentez la cinématique [Client credentials grant](produits-partages/documentation/utilisation-api-france-travail)
  * avec authentification, implémentez la cinématique [Authorization code flow](produits-partages/documentation/open-id-connect)

###  
Jetons

Selon la cinématique retenue, vous rencontrerez les types de jeton suivants :

Type de jeton| Cinématique| Description| Durée de validité  
---|---|---|---  
Access token| `Client credentials grant`  
`Authorization code flow`| C'est le jeton représentant l'autorisation donnée
au client. Il est utilisé pour tous les échanges entre l'application cliente
et le serveur de ressources afin d'accéder aux données.| 25 minutes  
Authorization code| Uniquement utilisé dans la cinématique `Authorization code
flow` (avec authentification utilisateur)| Émis par le serveur d'autorisation,
il indique le consentement de l'utilisateur et permet la récupération de
l'access token.| 60 secondes  
Id token| Uniquement utilisé dans la cinématique `Authorization code flow`
(avec authentification utilisateur)| C'est le jeton qui contient les
informations sur l'authentification de l'utilisateur final.| 2 heures et 30
minutes  
  
  
Un jeton peut cesser de fonctionner pour l'une des raisons suivantes :

  * sa durée de validité est dépassée
  * l'utilisateur connecté à votre application est revenu sur son consentement

Veillez à rendre votre code résilient en considérant ces événements.

###  
Scopes

Le scope est l’élément central de la gestion des accès à une API et à ses
ressources ; il caractérise un périmètre fonctionnel limité. Le développeur
d’une application interroge une API en précisant les scopes souhaités. L'usage
de certains scopes nécessite le consentement de l'utilisateur si la ressource
interrogée expose des données personnelles.

Le tableau suivant récapitule les scopes utilisés par France Travail :

Scope| Description| Exemple  
---|---|---  
api_[_Identifiant de l'API_][_Version_]| `Obligatoire`Permet d'autoriser votre
application à accéder à l'API correspondante (si plusieurs API, séparer ces
scopes par des espaces)| api_offresdemploiv2 o2dsoffre  
 _[Scopes applicatifs]_|  FacultatifPermet d'autoriser votre application à
accéder aux données métiers correspondantes, ils sont définis par API (si
plusieurs scopes applicatifs, séparer ces scopes par des espaces)| email
profile  
  


### Quota

Un mécanisme de gestion des quotas permet de réguler le nombre d'appels aux
API et d'optimiser le partage des ressources entre applications. Deux niveaux
de quotas sont déclinés :

  * Un quota maximum est défini pour chaque API, il permet d’assurer la disponibilité du service (exemple : l’API _Offres_ supporte une charge maximale de 100 appels par seconde, le quota maximum de cette API sera donc fixé à 100 appels par seconde)
  * Un quota maximum par application permet d'équilibrer le nombre de requêtes par application et par seconde entre toutes les applications (exemple : pour l’utilisation de l’API _Offres_ , chaque application dispose d’un quota maximum de 4 appels par seconde).

Ces quotas ne constituent en aucun cas un engagement de service, ils
contribuent au bon fonctionnement de l’écosystème.

En cas de dépassement d’un quota, une erreur HTTP 429 (Too Many Requests) est
retournée avec un en-tête `Retry-After` correspondant au nombre de secondes à
attendre avant d'être autorisé à réémettre la requête. Utilisez le dans vos
développements pour séquencer vos appels afin de garantir une continuité de
service à vos utilisateurs.

Dans la plupart des cas, le quota initial suffit à couvrir les besoins de nos
consommateurs. En cas de dépassement de quota, vérifiez que vous n'avez pas
fait d'[erreurs](produits-partages/documentation/erreurs-frequentes) dans
l'intégration de l'API à votre solution. Si toutefois ce quota vous parait
insuffisant pour le bon fonctionnement de votre service, vous pouvez demander
à l'augmenter à partir du [formulaire de contact](contact).

Avant d'effectuer une demande d’augmentation de quota, assurez-vous :

  * d'avoir correctement implémenté le mécanisme de `Retry-After`,
  * que vos requêtes soient cohérentes et correctement construites,
  * d'avoir un volume d’appels conséquent et régulier.

Nous surveillons et analysons régulièrement les requêtes de nos consommateurs
afin de détecter tout comportement qui nécessiterait une augmentation de
quota. Toute demande non justifiée ne sera pas traitée.



### Versionning

Les API sont versionnées.

Ainsi, la publication d'une API v3 provoque la dépréciation de l'API v2. Cette
dernière reste opérationnelle en attendant que l'ensemble des applications ait
migré sur la v3.

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

