# Démonstration du circuit Création : fiche d'HQC, 3e secondaire

Le même circuit que dans l'application, étape par étape :

| Fichier | Étape |
|---|---|
| `1-demande.json` | Demande construite à partir des données : 5 savoirs du thème « Premiers occupants du territoire » (HQC-P1-T01), opérations intellectuelles et critères du cadre d'évaluation, texte officiel de la réalité sociale comme seule source de faits, réglages, règles. Aucune donnée d'élève. |
| `2-reponse.json` | Réponse structurée de l'IA : documents rédigés pour la classe, 6 questions (chacune avec son opération, ses savoirs et son corrigé). |
| `3-validation.json` | Contrôles automatiques (`outils/valider_creation.py`) : opérations officielles, codes de savoirs, points, aucune citation attribuée, chaque nombre et chaque nom propre présent dans la source. Résultat : accepté. |
| `4-generer-docx.js` | Rendu en Word (dans l'application, ce rendu se fait dans le navigateur). |
| `fiche-hqc-sec3-premiers-occupants.docx` / `.pdf` | Le résultat : 3 pages (documents, questions avec lignes, corrigé avec critères et savoirs). |

Le validateur a aussi été essayé avec une réponse truquée (un chiffre et une citation inventés) : il l'a refusée.
