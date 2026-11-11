# Salle des profs

Plateforme québécoise pour les enseignantes et enseignants du primaire et du secondaire : planifier, créer, évaluer, observer. Spécialité : la correction d'épreuves manuscrites, conforme à la Loi 25, avec des données hébergées au Québec.

Évolution de Brûle la pile 1.0 (branche `ccr-fa15538c-lda5fe`, dossier `correcteur/`).

## Contenu

| Dossier | Contenu |
|---|---|
| `docs/` | Liste de vérification : décisions, architecture, Loi 25, pitch, phases |
| `donnees/` | Programme de formation en JSON : PDA et cadres d'évaluation |
| `outils/` | Scripts d'extraction des PDF du Ministère |
| `maquettes/` | Maquettes de l'interface (version retenue : `accueil-e-carnet-retenue.html`) |
| `correction/` | Code de correction, copié de la 1.0 |
| `gemini/` | Prompts pour Gemini et leurs résultats |

## Inventaire des documents officiels

`donnees/inventaire-pfeq.csv` : 402 PDF du ministère de l'Éducation (programmes, progressions des apprentissages, cadres d'évaluation), relevés le 10 novembre 2026 en lisant les pages de quebec.ca (`outils/inventaire_pfeq.py`). Chaque lien est réel.

La tentative de Gemini (`gemini/resultats/inventaire-pfeq-gemini-OBSOLETE.csv`) donnait 58 liens, tous vers l'ancien domaine education.gouv.qc.ca, et aucun ne correspondait à un document actuel : ne pas l'utiliser.

## Données du programme

| Fichier | Contenu |
|---|---|
| `pda-fra-primaire.json` | 1 188 savoirs, progression de la 1re à la 6e année, contenu prioritaire |
| `pda-mat-primaire.json` | 244 savoirs par domaine (rubriques Vocabulaire et Symboles à part) |
| `pda-mat-secondaire.json` | 426 savoirs, 6 champs ; colonne `primaire` (rappel des acquis de 6e année), puis 1re à 5e ; en 4e et 5e, valeur commune ou objet par séquence `CST`, `TS`, `SN` (154 savoirs) ; notes de la PDA dans `note_pda` ; formules en notation linéaire (`^` exposant, `_` indice) |
| `pda-st-ste-secondaire.json` | Science et technologie (ST) et Science et technologie de l’environnement (STE) : 611 savoirs, 6 univers ou parties ; colonnes `1`, `2`, `3`, `4` (ST) et `4-STE` ; `losange` : énoncé propre au programme obligatoire (73) ; stratégies `abordee_au_primaire` (lettre P) |
| `pda-ats-se-secondaire.json` | Applications technologiques et scientifiques (ATS) et Science et environnement (SE) : 558 savoirs ; colonnes `1` à `4` (ATS) et `4-SE` ; 41 losanges |
| `pda-chi-secondaire.json`, `pda-phy-secondaire.json` | Chimie (145 savoirs) et physique (134), programmes optionnels de 5e : colonnes `ATS-3`, `ATS-SE-4`, `ST-3`, `ST-STE-4`, puis `CHI-5` ou `PHY-5` ; `rappel` : énoncé non numéroté, déjà vu en 3e ou en 4e, avec sa `rubrique` ; stratégies : colonne `1er-cycle` en plus |
| `cadre-fra-primaire.json` | Compétences, critères, pondérations par cycle |
| `cadre-mat-primaire.json` | Compétences, critères, pondérations par cycle |
| `programme-hqc-secondaire.json` | Histoire du Québec et du Canada, 3e et 4e secondaire : 8 périodes, concepts, texte officiel de la réalité sociale, 103 thèmes et 427 éléments de connaissances, critères et 7 opérations intellectuelles du cadre (`outils/extraire_hqc.py`) |

### État des PDA (11 novembre 2026)

| Ordre | Validées (contrôle de logique sans erreur ou cas conformes au document) | À adapter |
|---|---|---|
| Primaire | Français, mathématique, science et technologie, univers social, éducation physique, art dramatique, arts plastiques, danse, musique | Anglais, langue seconde (colonne de catégories en plus, pages à image) ; Culture et citoyenneté québécoise (progression par cycle, crochets) |
| Secondaire | Art dramatique, arts plastiques, danse, éducation physique, musique, français langue seconde (base et enrichi), intégration linguistique, mathématique, sciences (ST, STE, ATS, SE), chimie, physique | Français (pages à image), univers social (géographie, histoire, monde contemporain, etc.), anglais, CCQ, espagnol |

Progression : `apprentissage` (flèche), `maitrise` (étoile), `reinvestissement` (case bleue), `null` (vide).

Sources : documents officiels du ministère de l'Éducation du Québec (Progression des apprentissages, 2009-2011 ; Cadres d'évaluation, 2011-04-21).

## Extraire une nouvelle discipline

```bash
python3 -I outils/extraire_pda.py PDA.pdf CODE "Discipline" primaire donnees/pda-code-primaire.json
```

Le script lit la structure du PDF : images des flèches et des étoiles, rectangles bleus, police grasse, retrait du texte. Les pages où les symboles sont intégrés dans une grande image sont signalées (`a_verifier`) ; on les fait lire visuellement par Gemini (voir `gemini/04-pda-fra-verification-images.txt`), puis on intègre avec contrôle croisé :

```bash
python3 -I outils/integrer_verification.py PDA.pdf donnees/pda.json reponse_gemini.json donnees/pda.json
```

**Mathématique au secondaire** : mise en page propre (colonnes qui se décalent d'une page à l'autre, cellules subdivisées par séquence, images des symboles décalées dans le PDF). Script à part, qui lit chaque cellule par pixels (l'étoile est symétrique gauche-droite, la flèche non) :

```bash
python3 -I outils/extraire_pda_math_sec.py PDA.pdf donnees/pda-mat-secondaire.json
```

Les PDA de science ont la même grille (deux documents couvrent les quatre programmes ; les deux PDF de chaque paire ont le même texte) :

```bash
python3 -I outils/extraire_pda_sciences_sec.py PDA-ST.pdf ST STE donnees/pda-st-ste-secondaire.json
python3 -I outils/extraire_pda_sciences_sec.py PDA-ATS.pdf ATS SE donnees/pda-ats-se-secondaire.json
```

Tirets des sous-énoncés et losanges lus par pixels eux aussi ; la dernière colonne (STE ou SE), plus large, va jusqu'au bord du tableau. Contrôle de logique : aucun écart.

Chimie et physique (colonnes de largeurs inégales, colonne « 1er cycle » en plus dans les stratégies, repérée d'après l'en-tête CHI ou PHY) :

```bash
python3 -I outils/extraire_pda_chimie_physique_sec.py PDA-chimie.pdf CHI donnees/pda-chi-secondaire.json
python3 -I outils/extraire_pda_chimie_physique_sec.py PDA-physique.pdf PHY donnees/pda-phy-secondaire.json
```

En mathématique, les 16 rangées à formule empilée, à racine dessinée ou à texte en image sont relues à la main (table `CORRECTIONS` du script). Le contrôle de logique laisse 17 écarts, tous conformes au document (ex. en probabilités, la séquence CST est vide en 4e et bleue en 5e).

Une ligne de Gemini est acceptée seulement si ses cases bleues et ses flèches concordent avec le PDF et si sa séquence est logique.

**Contrôle de logique à refaire après chaque extraction** : une progression doit suivre l'ordre flèches, étoile, cases bleues. Le 10 novembre, ce contrôle a révélé 144 étoiles manquantes en français (tranches d'images fusionnées à tort) et 2 lignes de mathématique fusionnées avec la rubrique Vocabulaire. Les deux bogues sont corrigés dans `outils/extraire_pda.py`.

Dépendances : `pdfplumber`, `pypdfium2`, `Pillow`.

## Remarque

`gemini/resultats/pda-mat-primaire-partie1-OBSOLETE.json` est une première tentative de Gemini par recherche web. Sa progression est erronée ; ne pas l'utiliser.

## Organisation

- Ce dépôt (`colorjazz/salle-des-profs`) contient **seulement la 2.0**. Son historique a été importé depuis le dossier `salle-des-profs/` de `colorjazz/bombe`.
- La 1.0 (Brûle la pile) reste dans `colorjazz/bombe`, déployée par Cloudflare depuis `main`, dossier `/correcteur`.
- `correction/` est une copie du code de correction de la 1.0 : elle évolue ici sans toucher à la 1.0.
- Une session Claude par dépôt, pour éviter que deux sessions modifient le même code en même temps.
