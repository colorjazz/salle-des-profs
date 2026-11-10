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
| `cadre-fra-primaire.json` | Compétences, critères, pondérations par cycle |
| `cadre-mat-primaire.json` | Compétences, critères, pondérations par cycle |
| `programme-hqc-secondaire.json` | Histoire du Québec et du Canada, 3e et 4e secondaire : 8 périodes, concepts, texte officiel de la réalité sociale, 103 thèmes et 427 éléments de connaissances, critères et 7 opérations intellectuelles du cadre (`outils/extraire_hqc.py`) |

### État des PDA (10 novembre 2026)

| Ordre | Validées (contrôle de logique sans erreur ou cas conformes au document) | À adapter |
|---|---|---|
| Primaire | Français, mathématique, science et technologie, univers social, éducation physique, art dramatique, arts plastiques, danse, musique | Anglais, langue seconde (colonne de catégories en plus, pages à image) ; Culture et citoyenneté québécoise (progression par cycle, crochets) |
| Secondaire | Art dramatique, arts plastiques, danse, éducation physique, musique, français langue seconde (base et enrichi), intégration linguistique | Français (pages à image), mathématique (colonnes par séquence), sciences (4 PDA), univers social (géographie, histoire, monde contemporain, etc.), chimie, physique, anglais, CCQ, espagnol |

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
