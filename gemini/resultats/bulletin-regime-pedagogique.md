# Analyse des règles du bulletin scolaire et de l'évaluation au Québec (Secteur public)

## Introduction
Ce document présente le cadre normatif officiel régissant le bulletin unique, l'évaluation des apprentissages et le calcul des résultats scolaires pour les ordres d'enseignement primaire et secondaire dans le secteur public au Québec. Il est conçu pour orienter la logique de calcul et l'architecture fonctionnelle d'un logiciel de suivi des résultats scolaires.

---

## 1. Les étapes de l'année scolaire et pondérations

### Réponse courte
L'année scolaire compte **trois étapes** officielles. Les pondérations réglementaires obligatoires pour le calcul du résultat final sont de **20 %** pour la première étape, **20 %** pour la deuxième étape et **60 %** pour la troisième étape. Une première communication écrite doit être transmise aux parents au plus tard le 15 octobre, et les dates limites de remise des bulletins sont fixées au 20 novembre, au 15 mars et au 10 juillet.

### Détails et Cadre Législatif
- **Cadre juridique :** Articles 29 et 30.2 du *Régime pédagogique de l'éducation préscolaire, de l'enseignement primaire et de l'enseignement secondaire* (RLRQ, c. I-13.3, r. 8).
- **Date de version citée :** Version consolidée à jour en date de 2026.
- **Répartition chronologique et pondérations :**
  - **Première communication :** Au plus tard le **15 octobre** (ne constitue pas un bulletin formel, mais renseigne sur l'adaptation ou le comportement).
  - **Étape 1 :** Pondération de **20 %** dans le résultat final de l'année. Date limite de transmission du bulletin : **20 novembre**.
  - **Étape 2 :** Pondération de **20 %** dans le résultat final de l'année. Date limite de transmission du bulletin : **15 mars**.
  - **Étape 3 :** Pondération de **60 %** dans le résultat final de l'année. Date limite de transmission du bulletin : **10 juillet** (généralement émis avant la fin des classes en juin).
- **Variations locales :** Les centres de services scolaires (CSS) fixent les dates exactes de fin d'étape au calendrier scolaire, mais doivent respecter les dates limites ministérielles de transmission des bulletins aux parents.

---

## 2. Calcul du résultat d'une compétence, du résultat disciplinaire et du résultat final

### Réponse courte
Le résultat d'une compétence à une étape se calcule à partir des évaluations formelles de l'étape. Le résultat disciplinaire s'obtient par la somme pondérée des compétences de la discipline (selon le cadre d'évaluation). Le résultat final de l'année combine les étapes selon la règle 20 % - 20 % - 60 %, en incluant le cas échéant les épreuves ministérielles (qui comptent généralement pour 20 % au primaire/secondaire inférieur et jusqu'à 50 % au secondaire 4 et 5).

### Détails et Cadre Législatif
- **Cadre juridique :** Articles 28, 30, 30.1, 30.2 et 30.3 du *Régime pédagogique*.
- **Date de version citée :** Version consolidée 2026.
- **Hiérarchie des calculs :**
  1. **Résultat par compétence (par étape) :** Basé sur les évaluations de la période ciblée. À l'étape 3, le résultat doit refléter l'ensemble des apprentissages de l'année, mais s'appuie principalement sur les évaluations de cette dernière période.
  2. **Résultat disciplinaire (par étape) :** Somme pondérée des compétences d'une même discipline, conformément aux pondérations officielles du *Cadre d'évaluation des apprentissages* de la matière.
  3. **Résultat final de l'année :** 
     $$\text{Résultat final} = (\text{Résultat étape 1} \times 0{,}20) + (\text{Résultat étape 2} \times 0{,}20) + (\text{Résultat étape 3} \times 0{,}60)$$
     *(Note : Pour les matières assujetties à une épreuve ministérielle ou obligatoire, le résultat de l'épreuve remplace ou se combine selon les directives spécifiques, par exemple 20 % ou 50 % de la note finale selon le niveau et le type d'épreuve).*
- **Seuil de réussite :** Fixé à **60 %** pour chaque matière (Art. 28.1).

---

## 3. Enseignement Primaire : Compétences au bulletin et regroupements

### Réponse courte
Au primaire, le bulletin unique présente à la fois un résultat disciplinaire, une moyenne de groupe et des résultats détaillés par compétence pour les matières principales (Français, Anglais langue seconde, Mathématique, Science et technologie). Certaines compétences y sont regroupées (ex. : *Lire* et *Apprécier* en arts).

### Détails et Cadre Législatif
- **Cadre juridique :** Articles 15 et 30 du *Régime pédagogique* et instructions annuelles du Ministère.
- **Date de version citée :** Version 2026.
- **Structure par cycle et matières :**
  - **Français, langue d'enseignement (Cycles 1, 2, 3) :** 
    - Lire / Apprécier des textes variés *(ou Lire)*
    - Écrire des textes variés *(ou Écrire)*
    - Communiquer oralement *(selon les étapes/cycles)*
  - **Mathématique (Cycles 1, 2, 3) :**
    - Résoudre une situation-problème
    - Utiliser un raisonnement mathématique
  - **Arts (Arts plastiques / Musique / Art dramatique) :** Les compétences *Réaliser des créations artistiques* et *Apprécier des œuvres d'art* sont souvent communiquées sous forme de résultats combinés ou par volet selon les instructions ministérielles.
  - **Éthique et culture religieuse / Éducation physique :** Compétences évaluées et rapportées selon le programme.
- **Non confirmé / Variable :** L'affichage exact des sous-volets à l'étape 1 ou 2 peut varier légèrement selon les adaptations technologiques du progiciel (ex. : Mozaïk-Portail) utilisé par le centre de services scolaire.

---

## 4. Enseignement Secondaire : Compétences, épreuves ministérielles et obligatoires

### Réponse courte
Au secondaire, chaque discipline présente des compétences spécifiques évaluées par étape. Les épreuves ministérielles (ou obligatoires) interviennent lourdement dans le calcul du résultat final de l'année : elles comptent pour 20 % pour certaines matières ciblées, et jusqu'à 50 % pour les épreuves uniques de fin de cycle (secondaire 4 et 5).

### Détails et Cadre Législatif
- **Cadre juridique :** Articles 30.2 et 30.3 du *Régime pédagogique*.
- **Date de version citée :** Version 2026.
- **Rôle des épreuves :**
  - Les épreuves obligatoires ou ministérielles ne modifient pas le calcul des notes des étapes 1 et 2. 
  - Pour l'étape 3, les notes de l'école ne doivent pas inclure l'épreuve ministérielle. C'est lors du calcul du **résultat final annuel** que l'épreuve entre en compte (ex. formule combinant la note de l'année et la note de l'épreuve unique selon la pondération officielle du cours, généralement 50/50 en fin de parcours secondaire pour les matières disciplinaires évaluées par le Ministère).
- **Variations :** La liste exacte des cours comportant une épreuve unique change chaque année selon les décrets ministériels.

---

## 5. Exigences sur le nombre de résultats et gestion des absences d'évaluation

### Réponse courte
Une compétence doit idéalement être évaluée à chaque étape pour refléter la progression. Si une compétence ne comporte aucun résultat à une étape en raison de circonstances exceptionnelles, des règles de pondération de rechange s'appliquent (généralement un report ou une redistribution des proportions entre les autres évaluations valides, encadrées par les normes et modalités de l'établissement).

### Détails et Cadre Législatif
- **Cadre juridique :** Politiques institutionnelles d'évaluation des apprentissages (PIEA) basées sur la Loi sur l'instruction publique et le Régime pédagogique.
- **Date de version citée :** Version 2026.
- **Règles logicielles à prévoir :**
  - Si un enseignant omet d'évaluer une compétence à l'étape 1 ou 2, le logiciel doit bloquer la validation ou exiger une justification (ex. : exemption pour élève HDAA avec plan d'intervention, Art. 30.4).
  - En cas d'absence non motivée à une épreuve obligatoire, la note de 0/20 ou 0 % est appliquée pour empêcher l'élève de tirer avantage de son absence.

---

## 6. Commentaires au bulletin

### Réponse courte
Les commentaires sont obligatoires pour certaines sections transversales (notamment à la 1re et à la 3e étape sur des compétences transversales ou le comportement), tandis qu'ils sont optionnels mais fortement encouragés pour individualiser le suivi disciplinaire.

### Détails et Cadre Législatif
- **Cadre juridique :** Articles du Régime pédagogique et instructions ministérielles annuelles (ex. *Instruction annuelle 2026-2027*).
- **Date de version citée :** Version 2026.
- **Exigences spécifiques :**
  - La section 3 du bulletin unique doit comporter, à la première et à la troisième étape, des commentaires qualitatifs sur au moins deux compétences transversales parmi quatre (ex. *Exercer son jugement critique*, *Organiser son travail*, *Savoir communiquer*, *Travailler en équipe*).
  - Des commentaires sur les forces, les défis et les progrès peuvent être ajoutés dans les rubriques disciplinaires (section 2).

---

## 7. Règles d'arrondi et présentation des moyennes de groupe

### Réponse courte
Les résultats inscrits au bulletin le sont sous forme de pourcentages entiers (arrondis à l'unité près). La moyenne de groupe doit également figurer à titre comparatif pour chaque discipline lorsque requis.

### Détails et Cadre Législatif
- **Cadre juridique :** Normes d'affichage du bulletin unique et directives ministérielles sur les formats de données.
- **Date de version citée :** Version 2026.
- **Règles logicielles :**
  - Utiliser l'arrondi mathématique standard (demi-up) vers l'entier le plus proche (ex. : 74,5 % devient 75 % ; 74,4 % devient 74 %).
  - Calculer la moyenne du groupe arithmétiquement à partir des notes finales non arrondies des élèves inscrits au groupe-classe, puis l'arrondir également à l'unité près pour l'affichage.

---

## 8. Changements récents (2020 à 2026) apportés au Régime pédagogique

### Réponse courte
Entre 2020 et 2026, les modifications ont principalement touché l'harmonisation complète du bulletin unique à l'échelle de la province, l'ajustement des modalités pour les élèves HDAA (plans d'intervention), ainsi que la mise à jour des programmes d'études et des grilles de dispensation horaire (notamment l'intégration progressive de nouveaux contenus en mathématiques, sciences et culture numérique).

### Détails et Cadre Législatif
- **Cadre juridique :** Modifications successives du *Régime pédagogique de l'enseignement primaire et secondaire* et instructions annuelles de la ministre de l'Éducation (notamment pour les rentrées 2024, 2025 et 2026).
- **Date de version citée :** 2026.
- **Points saillants pour le logiciel :** Stabilité de la structure du bulletin unique (étapes 20 % - 20 % - 60 %), renforcement des exigences pour l'adaptation des bulletins des élèves handicapés ou en difficulté (HDAA) via les plans d'intervention, et prise en charge des programmes adaptés (ex. CAPS-I, DÉFIS).

---

## Tableau Récapitulatif : Discipline | Ordre | Compétences au bulletin | Pondérations

| Discipline | Ordre d'enseignement | Compétences évaluées au bulletin | Pondérations usuelles des compétences (indicatif) |
| :--- | :--- | :--- | :--- |
| **Français, langue d'enseignement** | Primaire / Secondaire | 1. Lire / Apprécier<br>2. Écrire<br>3. Communiquer oralement | Variable selon le cycle (ex. : 40 % / 40 % / 20 %) |
| **Mathématique** | Primaire / Secondaire | 1. Résoudre une situation-problème<br>2. Utiliser un raisonnement mathématique | Variable selon le cycle (ex. : 30 % / 70 %) |
| **Anglais, langue seconde** | Primaire / Secondaire | 1. Interagir / Agir<br>2. Comprendre / Investir<br>3. Produire | Variable selon le programme de base ou enrichi |
| **Science et technologie** | Secondaire | 1. Mettre à profit des connaissances scientifiques<br>2. Mettre en œuvre la démarche scientifique | Selon le cadre d'évaluation spécifique |
| **Éducation physique et à la santé** | Primaire / Secondaire | Compétences axées sur le mouvement, la coopération et la santé | Établies par l'école / le cadre ministériel |