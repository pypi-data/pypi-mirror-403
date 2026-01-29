## Déconnecter l'utilisateur

Ce point d'accès vous permet de demander la déconnexion de l'utilisateur
auprès du serveur d'authentification de France Travail. La déconnexion est
réalisée sur _francetravail.fr_ avant que l'utilisateur soit redirigé sur une
page spécifique de votre application.

Un bouton de déconnexion doit être intégré dans votre application (France
Travail n'impose pas de contrainte ergonomique)

###  
Description de la requête

#### Point d'accès

Population d'utilisateurs| URL  
---|---  
Demandeurs d'emploi et candidats|

    
    
    GET https://authentification-candidat.francetravail.fr/compte/deconnexion  
  
Entreprises et recruteurs|

    
    
    GET https://entreprise.francetravail.fr/compte/deconnexion  
  
Agents|

    
    
    POST https://proxyproconnect.francetravail.net/connexion/oauth2/deconnexion  
  
####  
Détail des paramètres à valoriser

Corps de la requête| Valeur  
---|---  
id_token_hint| Valeur de l'id token  
(fourni suite à la génération d'un access token)  
redirect_uri| URL vers laquelle l'utilisateur sera redirigé une fois
déconnecté  
(encodée au format URL)  
  
####  
Exemple d'appel

    
    
    GET https://authentification-candidat.francetravail.fr/compte/deconnexion?id_token_hint=[Id token]&amp;amp;amp;amp;redirect_uri=[URL de redirection]

####  
Description de la redirection

Une fois la déconnexion réalisée sur _francetravail.fr_ , l'utilisateur est
redirigé sur la page de votre application indiquée dans le corps de la requête
(`redirect_uri`).

Vous devrez également supprimer toutes les informations fournies par le
serveur d'authentification de France Travail (données personnelles et jetons)
présentes dans sa session.



### Et maintenant ?

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

