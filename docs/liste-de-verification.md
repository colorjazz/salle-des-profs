# Salle des profs : liste de vérification

## Positionnement
- [ ] Spécialité : **correction d'épreuves manuscrites en pile**, au primaire et au secondaire au Québec
- [ ] Créneau libre : manuscrit + Loi 25 + compétences du PFEQ + Microsoft 365. Personne ne combine les quatre.
- [ ] Message : **« Le retour au papier, sans le fardeau de la correction »**. Une copie écrite en classe règle la question de l'élève qui triche avec l'IA.
- [ ] Concurrent québécois principal : **Scolaro** (numérique). Concurrent sur le manuscrit : **Examino** (France).

## Pitch de vente
- [ ] **Les enseignantes utilisent déjà l'IA pour corriger, dans des conditions périlleuses** : copies photographiées dans ChatGPT ou Gemini avec un compte personnel, noms des élèves visibles, traitement aux États-Unis, données parfois utilisées pour entraîner les modèles, aucune trace pour le centre de services.
- [ ] **Salle des profs encadre cet usage** : noms chiffrés, zone du nom rognée, IA à Montréal, validation par l'enseignante, journal d'accès, fichiers dans le OneDrive du centre de services.
- [ ] Message aux centres de services : **« Vous ne pouvez pas empêcher l'IA en correction. Vous pouvez l'encadrer. »**
- [ ] Message aux enseignantes : **« Le retour au papier, sans le fardeau de la correction. »**
- [ ] À documenter : des sondages ou articles sur l'usage de l'IA non encadrée par le personnel enseignant au Québec (recherche Gemini à faire).

## Confidentialité et Loi 25
- [ ] Règle d'or : **les résultats, jamais les copies**
- [ ] Deux circuits étanches : **Création** (sans renseignements personnels, n'importe quelle IA) et **Correction** (avec renseignements personnels, IA au Canada seulement)
- [ ] Les noms des élèves sont **chiffrés dans le navigateur**. Le serveur ne voit que des codes (« Élève 7F3A »).
- [ ] La zone du nom est **rognée** avant l'envoi de la copie à l'IA
- [ ] L'IA **propose**, l'enseignante **valide** (article 12.1)
- [ ] Récupération de la clé : code imprimé, passkey et copie dans le OneDrive ; copie chiffrée à l'école en option
- [ ] À prévoir : EFVP, responsable de la protection des renseignements personnels désigné, registre des incidents, journal d'accès, politique en langage clair, exportation et suppression des données, durée de conservation
- [ ] Moins de 14 ans : le consentement passe par le titulaire de l'autorité parentale
- [ ] Vendre à l'enseignante seule est légalement fragile : **viser les centres de services**

## Infrastructure
- [ ] **Faire évoluer Brûle la pile 1.0**, pas repartir à zéro
- [ ] On garde : le Worker Cloudflare, le JavaScript pur sans compilation, le déploiement à chaque push, Stripe, l'admin, la traduction, la caméra, le redressement des photos, les annotations, la PDA, les prompts et schémas JSON
- [ ] D1 sert **seulement** à la facturation, aux clés et crédits, au parrainage, à l'admin et au journal des appels à l'IA. **Aucune donnée d'élève.**
- [ ] Nouveau : **Postgres à Montréal** (Supabase ou Neon, région ca-central-1) par Hyperdrive, **cache désactivé**
- [ ] Correction avec Gemini par Vertex AI, **région Montréal**, et un modèle de secours **dans la même région**
- [ ] Courriels de connexion envoyés depuis le Canada (AWS SES Montréal)
- [ ] Les clés `CE-XXXXX` deviennent le portefeuille de crédits d'un compte
- [ ] Dans le navigateur : QR, PDF, PPT et chiffrement
- [ ] Copies : sur le même appareil d'abord (option A) ; dépôt temporaire chiffré plus tard (option B)

## Microsoft 365
- [ ] Connexion Microsoft **et** lien magique en secours
- [ ] Permissions minimales : connexion, courriel, et **dossier de l'application** dans OneDrive
- [ ] Copies, listes de noms, exportations et sauvegarde de clé dans le **OneDrive de l'enseignante**. Le centre de services en est le gardien.
- [ ] Exportations en formats natifs : Word, PowerPoint, Excel
- [ ] Une seule application pour tous les centres de services (application Microsoft multi-organisations)
- [ ] Obtenir la **vérification d'éditeur Microsoft** (il faut une entreprise enregistrée)
- [ ] Plus tard : importation des groupes, Teams. Mozaïk directement : pas au début.

## Design
- [ ] **Jamais d'emoji** dans l'interface
- [ ] Convivialité inspirée de Mozaïk-Portail : épurée, relaxante, beaucoup d'espace blanc, couleurs douces
- [ ] Quatre volets dans la navigation : **Planifier, Créer, Évaluer, Observer**
- [ ] Filtres groupe, matière et étape en haut de la page
- [x] Style retenu : **Carnet** (papier crème, terre cuite, titres à empattements), avec le tableau « Évaluations en cours » de la version barre latérale. Maquette : `maquettes/accueil-e-carnet-retenue.html`
- [ ] Carte « Mon horaire et mon calendrier » sur l'accueil :
  - [ ] Horaire **par jour de la semaine** par défaut (titulaires du primaire) ; cycle de 9 ou 10 jours en option (spécialistes, secondaire)
  - [ ] Importer l'horaire : PDF, Excel ou photo, lu par l'IA du circuit Création (aucune donnée d'élève)
  - [ ] Importer le calendrier scolaire du centre de services (journées pédagogiques, congés, fins d'étape) : PDF, .ics ou Excel
  - [ ] Petit calendrier du mois sous l'horaire : aujourd'hui, journées pédagogiques, évaluations prévues (reliées à la liste « À venir »)
  - [ ] Option « Connecter Outlook » plus tard : demande la permission Calendars.Read, donc une approbation de plus pour les TI

## Fonctionnalités clés
- [ ] **QR code par élève** sur chaque copie imprimée, puis numérisation de la pile et tri automatique
- [ ] **Correction question par question**, avec regroupement des réponses semblables
- [ ] **Barème dynamique**, recalculé de façon rétroactive
- [ ] Commentaire **« une force, un défi »**
- [ ] **Tendances de la classe**, avec un bouton « Créer une activité de récupération » selon la PDA. Aucun concurrent ne fait ce lien.
- [ ] Tableau de bord : **progression des compétences** par élève et par groupe
- [ ] Pas de détecteur d'IA

## Fournisseur de l'IA (recherche Azure du 10 novembre)
- [x] Azure OpenAI au Canada : écarté pour l'instant. Les modèles à l'usage avec traitement garanti à Québec (gpt-4o, gpt-4.1-mini) ont été retirés en octobre 2026 ; GPT-5 à Québec seulement en capacité réservée (plusieurs milliers $/mois) ; Toronto n'offre rien en régional.
- [x] Fournisseur retenu : **Gemini sur Vertex AI à Montréal**
- [ ] À vérifier dans le portail Azure avant de clore (la disponibilité change souvent) : un modèle remplaçant en déploiement Standard régional à Canada East ?
- [ ] Piste : **Azure AI Document Intelligence (Read) à Québec** pour placer les surlignages exactement sur les mots (boîtes de chaque mot manuscrit). Ajoute un sous-traitant (Microsoft) à l'EFVP. À mesurer avec `tools/surlignages` de la 1.0.
- [ ] Si Azure est utilisé un jour : demander la surveillance des abus modifiée (aucune conservation des copies)

## Volet Créer
- [x] Qualité de référence validée : activité Word (Confédération) et présentation PowerPoint (Révolution tranquille), dans `exemples/`
- [x] Programme d'Histoire du Québec et du Canada extrait (`donnees/programme-hqc-secondaire.json`) : 427 éléments, tous vérifiés dans le texte du PDF
- [ ] Extraire les 37 autres PDA et les cadres d'évaluation (inventaire : `donnees/inventaire-pfeq.csv`)
- [ ] Gabarits Word et PowerPoint dans le navigateur (pptxgenjs, docx)
- [ ] Contrôle automatique : aucune citation inventée, dates dans la période, savoirs existants

## Idée : espace « Suppléance »
- [ ] Un endroit où l'enseignante prépare d'avance du matériel pour son remplacement (absence prévue ou imprévue)
- [ ] Contenu : exercices à imprimer, activité autonome, consignes pour la suppléante, plan de la journée tiré de l'horaire, corrigé
- [ ] Basé sur la planification : ce qui est prévu cette semaine selon la PDA, en révision (savoirs déjà vus), sans nouvelle notion
- [ ] Une « trousse d'urgence » toujours prête pour une absence imprévue, avec impression en un clic
- [ ] Partage à la suppléante ou à la direction sans compte (lien ou PDF), et aucun nom d'élève dans le matériel
- [ ] Lié à la clé de groupe partagée (spécification, section 5) si la suppléante doit voir la liste des élèves
- [ ] **Absence imprévue : une personne en autorité (direction adjointe) peut générer la trousse elle-même**
  - [ ] Rôle « direction » dans l'école : accès à l'horaire, à la planification et au matériel de l'enseignante, sans les noms des élèves ni les résultats
  - [ ] Elle choisit le groupe et la journée ; la trousse se bâtit à partir de la planification (révision de notions déjà vues) et de la trousse d'urgence, si elle existe
  - [ ] Chaque génération est inscrite au journal d'accès, et l'enseignante en est avisée
  - [ ] L'enseignante peut désactiver cet accès ou préparer d'avance ses consignes de suppléance

## Phases
- [ ] **Première version :** groupes chiffrés, évaluation imprimable avec QR, numérisation, correction IA validée par l'enseignante, connexion Microsoft et courriel, OneDrive
- [ ] **Phase 2 :** tableau de bord des compétences, importation des groupes par Microsoft
- [ ] **Phase 3 :** création de matériel (plan de leçon, PPT, activités), Teams

## Centre de services (en parallèle du développement)
- [ ] Ordre d'approche : **conseillère pédagogique ou RÉCIT**, ensuite les **TI**, ensuite le **responsable de la protection des renseignements personnels**
- [ ] Demander un **avis**, pas une vente. Montrer la 1.0 en 5 minutes.
- [ ] Questions à poser :
  - [ ] Les enseignantes peuvent-elles consentir elles-mêmes à une application Microsoft ?
  - [ ] Quel est le processus d'approbation d'un outil, et en combien de temps ?
  - [ ] Existe-t-il un modèle d'EFVP ou des exigences pour les fournisseurs ?
  - [ ] Les groupes sont-ils synchronisés de Mozaïk vers Teams ?
  - [ ] Peut-on importer des notes dans Mozaïk-Portail à partir d'un fichier ?
  - [ ] Seriez-vous ouverts à un pilote gratuit ?
- [ ] Délai réaliste pour un premier centre de services : **3 à 9 mois**

## Vérifications techniques (recherche 4)
- [x] D1 et R2 : **pas de juridiction au Canada**. D1 = facturation seulement, confirmé.
- [x] Hyperdrive : le cache peut être désactivé (`--caching-disabled`)
- [x] **Supabase à Montréal (ca-central-1) retenu.** Neon écarté (pas de région au Canada).
- [x] OneDrive des organisations canadiennes : stocké au Canada (Toronto et Québec)
- [x] `Files.ReadWrite.AppFolder` possible seul
- [x] Consentement utilisateur bloqué presque partout : **approbation des TI nécessaire**
- [x] Vérification d'éditeur : passe par le programme partenaire de Microsoft (Partner One ID). Il faut une entreprise enregistrée.
- [x] AWS SES à Montréal : disponible, retenu
- [x] Le point d'accès Gemini « global » **ne garantit pas** la résidence des données. Il faut le point d'accès régional.
- [x] **Gemini répond à Montréal (northamerica-northeast1)**. Testé. Toute la correction peut rester au Québec.
- [x] Modèles à Montréal : **seul gemini-3.5-flash** y est offert (constat de la 1.0, 28 octobre 2026). 3.7-flash non. Surlignages exacts : 75 % à Montréal contre 84 % ailleurs.
- [x] La 1.0 appelle **Google AI Studio par défaut** (sans garantie de pays). Montréal est une option (`X-Region: qc`), sans repli ailleurs quand elle est cochée.
- [ ] Dans la 2.0 : **forcer le point d'accès régional de Montréal** partout. Plus d'API compatible OpenAI ni de point d'accès global pour le circuit de correction.

## À faire maintenant
- [x] Lancer la **recherche 4** dans Gemini (vérifications techniques)
- [x] Point d'accès de la 1.0 vérifié : AI Studio par défaut, Vertex Montréal en option
- [x] Spécification technique v0.1 : `docs/specification-technique.md`
- [ ] Essayer **Examino** et **Scolaro**, et comparer avec la 1.0 sur les mêmes copies
- [ ] Lancer la **recherche 3** (Loi 25) avant le café avec la conseillère pédagogique
- [ ] Plus tard : recherches 2, 5 et 6
- [ ] Quand vous aurez des crédits : une fiche d'une page, une fiche technique pour les TI et un brouillon d'EFVP

## Idée : « Le balado du lundi »
- [ ] Un résumé audio d'une ou deux minutes, le lundi matin, de ce qui s'en vient dans la semaine : réunions, remise des notes, récupération, surveillances, activités sur l'heure du midi
- [ ] Une version texte accompagne l'audio (accessibilité, écoute impossible en classe)
- [ ] Trois sources possibles, au choix :
  - [ ] **L'équipe de direction** : elle publie les événements de l'école pour tout le personnel
  - [ ] **La direction de niveau** : des messages ciblés pour un niveau ou un cycle
  - [ ] **Les courriels de l'usager**, s'il active l'option : l'IA en extrait les dates et les tâches
- [ ] Personnalisé avec l'horaire de l'enseignante (ses surveillances, ses périodes de récupération) et sa planification (évaluations prévues, notes à remettre)
- [ ] **Courriels : attention.** Il faut la permission Microsoft `Mail.Read`, bien plus large que le dossier de l'application. Option désactivée par défaut, consentement explicite, approbation des TI, traitement au Canada seulement, aucun courriel conservé (seulement les événements extraits)
- [ ] Les courriels peuvent contenir des renseignements sur des élèves (parents, plans d'intervention) : le résumé ne doit jamais nommer d'élève
- [ ] Voix de synthèse en français québécois ; vérifier qu'un service de synthèse vocale est offert dans la région de Montréal
- [ ] Argument de vente : la direction rejoint tout son personnel en deux minutes, au lieu d'un courriel du dimanche soir que personne ne lit
