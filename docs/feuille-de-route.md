# Salle des profs : feuille de route vers un site pleinement opérationnel

État au 12 novembre 2026. Le site en ligne (salledesprofs.netlify.app) est une **maquette** : les pages sont belles et les données du programme sont réelles, mais il n'y a ni comptes, ni sauvegarde, ni appel à l'IA. Cette liste décrit tout ce qu'il faut pour passer de la maquette au produit.

Légende : **[Vous]** = démarche à faire par vous (entreprise, contrats, contacts) · **[Code]** = travail de développement · **[Gemini]** = tâche longue à confier à Gemini.

---

## Étape 0. Déjà fait

- [x] Maquettes des volets Planifier (avec Suppléance), Créer (complet) et Évaluer (copie, correction), accueil retenu, version téléphone
- [x] Police Lexend hébergée sur le site, sans appel à Google
- [x] Les 36 PDA francophones extraites et vérifiées (10 551 savoirs), le catalogue et les modules
- [x] Choix du niveau et de la matière qui fonctionne partout dans les maquettes
- [x] Circuit Création démontré de bout en bout (fiche HQC 3e secondaire) avec un validateur
- [x] Code de correction de la 1.0 copié dans `correction/`
- [x] Décisions d'architecture : Supabase à Montréal, Supabase Auth, Gemini sur Vertex à Montréal, AWS SES à Montréal

---

## Étape 1. Fondations administratives et légales [Vous]

Ce qui bloque le reste, surtout la vente aux centres de services et la connexion Microsoft.

- [ ] **Enregistrer l'entreprise** (NEQ au Registraire des entreprises). C'est requis pour la vérification d'éditeur Microsoft, les contrats et la facturation.
- [ ] Acheter un **nom de domaine** (ex. salledesprofs.ca) et une adresse courriel professionnelle
- [ ] Ouvrir les comptes fournisseurs au nom de l'entreprise :
  - [ ] Supabase (projet en région **ca-central-1**)
  - [ ] Google Cloud (Vertex AI, région **northamerica-northeast1**), avec alerte de budget
  - [ ] AWS (SES à Montréal) pour les courriels de connexion
  - [ ] Cloudflare (Worker) ; Stripe existe déjà avec la 1.0
- [ ] S'inscrire au **programme partenaire Microsoft** (Partner One ID), puis demander la vérification d'éditeur
- [ ] Désigner le **responsable de la protection des renseignements personnels** (vous, au début) et publier son titre et ses coordonnées
- [ ] Rédiger, avec un juriste idéalement :
  - [ ] la **politique de confidentialité** en langage clair
  - [ ] les **conditions d'utilisation**
  - [ ] un **modèle d'entente** avec un centre de services (sous-traitance, Loi 25, durée de conservation, fin de contrat)
- [ ] Préparer le **brouillon d'EFVP** (évaluation des facteurs relatifs à la vie privée) et la fiche technique pour les TI
- [ ] Envisager une **assurance responsabilité professionnelle et cyberrisques**

## Étape 2. Le socle technique [Code]

Jalon J1 de la spécification. Rien de visible pour l'enseignante, mais tout repose dessus.

- [ ] Créer le **Worker Cloudflare de la 2.0**, déployé depuis ce dépôt à chaque push, sur le nom de domaine
- [ ] Créer la **base Postgres à Montréal** (tables de la spécification, section 4) et la relier par Hyperdrive, cache désactivé
- [ ] **Comptes** : Supabase Auth avec lien magique (courriels par SES à Montréal), sessions sécurisées
- [ ] Servir le **catalogue** (PDA, modules) depuis le Worker ou la base
- [ ] En-têtes de sécurité (CSP, HSTS), limites de requêtes, aucun contenu de copie dans les journaux
- [ ] **Journal d'accès** et **registre des incidents**
- [ ] Sauvegardes automatiques de la base et un test de restauration
- [ ] Passer les maquettes en vraies pages : remplacer les données d'exemple par celles du compte

## Étape 3. Le coffre et les groupes [Code]

Jalon J2. Le cœur de la promesse Loi 25.

- [ ] Phrase secrète, **code de récupération imprimé**, clé d'accès (passkey)
- [ ] **Chiffrement des noms dans le navigateur** ; le serveur ne voit que « Élève 7F3A »
- [ ] Importation d'une liste d'élèves (CSV ou Excel), chiffrée avant l'envoi
- [ ] Clé de groupe partagée (coenseignante, suppléante)
- [ ] Exportation et suppression complète des données d'un compte

## Étape 4. Volet Évaluer : la correction des copies manuscrites [Code]

Jalons J3 à J5. C'est la spécialité qui fait vendre.

- [ ] Créer une évaluation liée aux critères du cadre d'évaluation et aux savoirs de la PDA
- [ ] **PDF imprimable** avec un QR par élève et une zone du nom
- [ ] **Numérisation de la pile** (caméra ou numériseur), tri automatique par QR, redressement des photos
- [ ] **Rognage de la zone du nom** avant tout envoi à l'IA
- [ ] Appel à **Gemini sur Vertex à Montréal, sans repli hors région** (une seule fonction qui refuse toute autre région)
- [ ] Correction **question par question**, regroupement des réponses semblables, **validation par l'enseignante**
- [ ] Barème dynamique recalculé, commentaire « une force, un défi »
- [ ] Exportation des résultats en Excel (format importable dans Mozaïk-Portail, à vérifier avec le centre de services)
- [ ] Mesurer la qualité à Montréal avec `tools/surlignages` de la 1.0 et améliorer les prompts

## Étape 5. Volet Créer : brancher l'IA [Code]

La maquette est complète ; il manque le vrai moteur.

- [ ] Point d'entrée du Worker pour le **circuit Création** (Gemini, aucune donnée d'élève)
- [ ] Porter `outils/valider_creation.py` en JavaScript dans le Worker : aucune citation inventée, savoirs existants, points exacts, faits présents dans la source
- [ ] Génération **Word et PowerPoint dans le navigateur** (docx, pptxgenjs), à partir du modèle de la fiche HQC
- [ ] Les sept types : fiche, activité, présentation, évaluation, dictée, lecture, et les modèles
- [ ] **Bibliothèque** personnelle sauvegardée, partage entre collègues, enregistrement dans OneDrive
- [ ] **Quota d'IA par licence** et journal des coûts (D1)

## Étape 6. Volet Planifier [Code]

- [ ] Planification annuelle sauvegardée (savoirs par étape, à partir des modules)
- [ ] **Horaire** : par jour de la semaine ou cycle de 9 ou 10 jours ; importation par PDF, Excel ou photo
- [ ] **Calendrier scolaire** du centre de services (journées pédagogiques, fins d'étape)
- [ ] **Suppléance** : trousse d'urgence, impression en un clic, partage sans compte, aucun nom d'élève
- [ ] **Rôle « direction »** : générer la trousse lors d'une absence imprévue, inscrit au journal d'accès, enseignante avisée

## Étape 7. Volet Observer [Code]

Jalon J7. Aucune maquette encore.

- [ ] **Maquetter** le volet Observer
- [ ] Progression des compétences par élève et par groupe
- [ ] Tendances de la classe avec « Créer une activité de récupération » (lien vers Créer)
- [ ] Respect des règles du bulletin (spécification, section 7)

## Étape 8. Microsoft 365 [Code + Vous]

Jalon J6. Dépend de l'entreprise enregistrée (étape 1).

- [ ] Application Entra multi-organisations : connexion Microsoft, permissions minimales (`Files.ReadWrite.AppFolder`)
- [ ] Enregistrement des copies, listes, exportations et sauvegarde de clé dans le **OneDrive de l'enseignante**
- [ ] Vérification d'éditeur obtenue
- [ ] Plus tard : importation des groupes, Teams, Outlook (calendrier)

## Étape 9. Contenu pédagogique [Gemini + Vous]

- [ ] **Modules conviviaux** des 33 matières restantes (prompt `gemini/11-modules-et-libelles.txt`), à commencer par MAT, FRA, ST et HQC au secondaire
- [ ] Extraire les **cadres d'évaluation** (critères) de toutes les matières ; seuls ceux de HQC sont utilisés pour l'instant
- [ ] Petits programmes : projet personnel d'orientation, entrepreneuriat, projet intégrateur
- [ ] Faire relire les modules par une ou deux enseignantes par matière (ou une conseillère pédagogique)
- [ ] Plus tard : les programmes du secteur anglophone

## Étape 10. Qualité avant le lancement [Code]

- [ ] Tests automatiques des parcours clés (connexion, coffre, correction, création)
- [ ] **Révision de sécurité** complète, double authentification des comptes administratifs
- [ ] **Accessibilité** (contraste, clavier, lecteur d'écran) : un argument auprès des centres de services
- [ ] Essais sur téléphone, tablette, Chromebook et les navigateurs des écoles
- [ ] Surveillance des pannes et des coûts, page d'état du service
- [ ] Comparer avec **Examino** et **Scolaro** sur les mêmes copies

## Étape 11. Pilote et vente [Vous]

- [ ] Café avec une **conseillère pédagogique ou le RÉCIT**, puis les TI, puis le responsable de la protection des renseignements personnels
- [ ] **Pilote gratuit** avec quelques enseignantes d'une école
- [ ] Site public : présentation, tarifs, politique de confidentialité, aide
- [ ] Guide de démarrage et courtes vidéos
- [ ] Adresse de soutien et délai de réponse
- [ ] **Console d'administration** du centre de services (licences, utilisation agrégée) et facturation sur facture
- [ ] Premier contrat (délai réaliste : 3 à 9 mois)

---

## Ordre suggéré

1. **Tout de suite, en parallèle :** étape 1 (entreprise, domaine, comptes) [Vous] et étape 9, modules Gemini [Gemini].
2. **Ensuite :** étapes 2 et 3 (socle, coffre). Sans elles, rien ne se sauvegarde.
3. **Le cœur de la vente :** étape 4 (Évaluer), puis le pilote (étape 11) avec la correction seule.
4. **Pendant le pilote :** étapes 5 et 6 (Créer, Planifier), puis 7 (Observer) et 8 (Microsoft).
5. **Avant le premier contrat :** étape 10 (qualité, sécurité, accessibilité).

Une première version utile pour un pilote = étapes 1 à 4, plus Créer en mode simple. Les autres volets peuvent rester en « bientôt ».
