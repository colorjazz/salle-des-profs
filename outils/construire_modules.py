"""Construit les modules : des regroupements de savoirs de la PDA, avec un titre et une phrase en langage clair.

Un module regroupe des savoirs voisins (« Les fractions », « Accorder le verbe avec son sujet »).
L'enseignante choisit d'abord un module, puis, au besoin, des savoirs précis. Le texte officiel et les
codes restent intacts dessous.

Trois sources, par ordre de priorité :
1. modules/<ordre>-<code>.json rédigés (ici ou par Gemini, voir gemini/11) : titres et descriptions
   choisis, et règles d'affectation ;
2. règles écrites dans ce fichier (français et mathématique au primaire, HQC) ;
3. à défaut, modules automatiques tirés du premier niveau des sections de la PDA, titres nettoyés.
Chaque savoir appartient à un seul module ; le script le vérifie.
Usage : python3 -I outils/construire_modules.py donnees maquettes/catalogue
"""
import json, os, re, sys, glob, collections


def propre(t):
    t = re.sub(r'\s*\(P\d.*$', '', t or '')                     # renvois aux pages du programme
    t = re.sub(r'^([A-Z]|\d{1,2}|[ivx]+)\.\s*', '', t.strip())   # marqueurs de liste
    t = re.sub(r'(?<=[a-zé])\d+\b', '', t)                       # appels de note
    t = re.sub(r'\s+', ' ', t).strip(' :')
    if t.isupper() or sum(c.isupper() for c in t) > len(t) * .6:
        t = t[:1] + t[1:].lower()
    return t[:1].upper() + t[1:]


# ---------- règles rédigées (modèles pour les autres matières) ----------
def regles_fra_primaire(s):
    c, sec, ch0 = s.get('competence', ''), s.get('section') or '', ((s.get('chemin') or [''])[0]).lower()
    if c.startswith('Lire'):
        return 'lire-strategies' if 'stratég' in ch0 else 'lire-textes'
    if c.startswith('Apprécier'):
        return 'apprecier'
    if c.startswith('Communiquer'):
        return 'oral-strategies' if 'stratég' in ch0 else 'oral-connaissances'
    if sec == 'Accords':
        if 'classes de mots' in ch0: return 'classes-mots'
        if 'pluriel' in ch0 or 'féminin' in ch0: return 'feminin-pluriel'
        if 'groupe du nom' in ch0: return 'accords-gn'
        if 'sujet' in ch0: return 'accord-verbe'
        return 'reviser-accords'
    if sec == 'Syntaxe et ponctuation':
        if 'ponctuation' in ch0: return 'ponctuation'
        if 'groupe du nom' in ch0 or 'fonctions' in ch0: return 'groupes-fonctions'
        return 'phrase'
    if sec == 'Conjugaison': return 'conjugaison'
    if sec == 'Orthographe d’usage': return 'orthographe'
    if sec == 'Lexique': return 'dictionnaire' if 'dictionn' in ch0 else 'mots'
    if sec.startswith('Organisation'): return 'organiser-texte'
    return 'ecrire-autres'

MODULES_FRA_PRIMAIRE = [
    ('lire-textes', 'Comprendre les textes', 'Reconnaître les genres de textes, leur structure et ce qui fait avancer une histoire.'),
    ('lire-strategies', 'Les stratégies de lecture', 'Se préparer à lire, vérifier sa compréhension et surmonter un obstacle dans un texte.'),
    ('apprecier', 'Apprécier les œuvres', 'Découvrir des œuvres littéraires, en parler et justifier ses goûts de lecteur.'),
    ('classes-mots', 'Les classes de mots', 'Reconnaître le nom, le déterminant, l’adjectif, le verbe, le pronom et les mots invariables.'),
    ('feminin-pluriel', 'Le féminin et le pluriel', 'Former le féminin et le pluriel des noms et des adjectifs, y compris les cas particuliers.'),
    ('accords-gn', 'Les accords dans le groupe du nom', 'Accorder le déterminant et l’adjectif avec le nom, en genre et en nombre.'),
    ('accord-verbe', 'Accorder le verbe avec son sujet', 'Trouver le sujet, puis accorder le verbe en personne et en nombre.'),
    ('reviser-accords', 'Réviser ses accords', 'Relire son texte pour repérer et corriger ses erreurs d’accord.'),
    ('phrase', 'La phrase et ses types', 'Construire des phrases déclaratives, interrogatives et exclamatives, positives et négatives.'),
    ('groupes-fonctions', 'Les groupes et leurs fonctions', 'Repérer le groupe du nom, le sujet et le prédicat dans la phrase.'),
    ('ponctuation', 'La ponctuation', 'Utiliser la majuscule, le point et la virgule pour rendre ses phrases claires.'),
    ('conjugaison', 'Conjuguer les verbes', 'Connaître les temps de conjugaison, les verbes modèles et se bâtir un aide-mémoire.'),
    ('orthographe', 'Bien écrire les mots', 'Mémoriser l’orthographe des mots de la liste et vérifier ses doutes.'),
    ('mots', 'Le sens et la formation des mots', 'Comprendre comment les mots se forment et les liens qui les unissent (synonymes, familles).'),
    ('dictionnaire', 'Utiliser le dictionnaire', 'Trouver un mot, comprendre un article et choisir le bon sens.'),
    ('organiser-texte', 'Organiser son texte', 'Planifier son texte, le découper en paragraphes et assurer sa cohérence.'),
    ('ecrire-autres', 'Écrire : autres apprentissages', 'Les autres connaissances et stratégies utiles en écriture.'),
    ('oral-connaissances', 'Prendre la parole et écouter', 'Les connaissances utiles pour s’exprimer et écouter : intention, vocabulaire, prononciation.'),
    ('oral-strategies', 'Les stratégies à l’oral', 'S’exprimer avec aisance, réagir aux propos des autres et ajuster ses paroles.'),
]


def regles_mat_primaire(s):
    c, sec, ch0 = s.get('competence', ''), s.get('section') or '', ((s.get('chemin') or [''])[0]).lower()
    if c == 'Arithmétique':
        if 'fraction' in ch0: return 'fractions'
        if 'décima' in ch0: return 'decimaux'
        if 'entiers' in ch0: return 'entiers'
        return 'operations' if 'pération' in sec else 'naturels'
    if c == 'Géométrie':
        return 'frises' if 'frise' in ch0 else ('solides' if 'solide' in ch0 else ('figures' if 'figure' in ch0 else 'espace'))
    if c == 'Mesure':
        return 'temps' if 'temps' in ch0 else ('longueurs' if 'longueur' in ch0 or 'surface' in ch0 or 'volume' in ch0 else 'autres-mesures')
    return 'statistique' if c == 'Statistique' else ('probabilite' if c.startswith('Probabilit') else 'autres')

MODULES_MAT_PRIMAIRE = [
    ('naturels', 'Les nombres naturels', 'Lire, écrire, comparer et décomposer les nombres, selon la grandeur prévue pour l’année.'),
    ('operations', 'Les opérations', 'Additionner, soustraire, multiplier et diviser, mentalement, par écrit ou avec du matériel.'),
    ('fractions', 'Les fractions', 'Représenter, lire, comparer et reconnaître des fractions équivalentes.'),
    ('decimaux', 'Les nombres décimaux', 'Comprendre les dixièmes, les centièmes et les millièmes, et calculer avec eux.'),
    ('entiers', 'Les nombres entiers', 'Découvrir les nombres négatifs, par exemple sur un thermomètre.'),
    ('espace', 'Se repérer dans l’espace', 'Situer des objets, utiliser un plan et un système de repérage.'),
    ('solides', 'Les solides', 'Reconnaître, décrire et construire des solides.'),
    ('figures', 'Les figures planes', 'Nommer, décrire et classer les figures planes et leurs propriétés.'),
    ('frises', 'Frises et dallages', 'Créer des frises et des dallages par réflexion et par translation.'),
    ('longueurs', 'Longueurs, surfaces et volumes', 'Estimer et mesurer avec des unités conventionnelles.'),
    ('temps', 'Le temps', 'Lire l’heure, mesurer des durées et utiliser le calendrier.'),
    ('autres-mesures', 'Angles, masses, capacités, températures', 'Comparer et mesurer avec les bons instruments.'),
    ('statistique', 'La statistique', 'Poser une question, recueillir des données et les présenter dans un tableau ou un diagramme.'),
    ('probabilite', 'Le hasard et les probabilités', 'Prédire si un résultat est certain, possible ou impossible, puis le vérifier.'),
    ('autres', 'Autres apprentissages', 'Les autres connaissances de mathématique.'),
]

REGLES = {('primaire', 'FRA'): (regles_fra_primaire, MODULES_FRA_PRIMAIRE),
          ('primaire', 'MAT'): (regles_mat_primaire, MODULES_MAT_PRIMAIRE)}


def modules_auto(sv_complets):
    """Premier niveau des sections de la PDA, titres nettoyés ; les groupes d'un ou deux savoirs rejoignent un voisin."""
    cle = lambda s: (s.get('competence') or s.get('champ') or s.get('theme') or s.get('enjeu') or '', ((s.get('chemin') or [''])[0]))
    groupes = collections.OrderedDict()
    for s in sv_complets:
        groupes.setdefault(cle(s), []).append(s['id'])
    modules, affectation, precedent = [], {}, {}
    for (g, c), ids in groupes.items():
        titre = propre(c) or propre(g)
        if len(ids) <= 2 and g in precedent:
            m = precedent[g]
        else:
            m = f"m{len(modules) + 1:02d}"
            modules.append({'id': m, 'titre': titre, 'description': propre(g) if c else '', 'auto': True})
            precedent[g] = m
        for i in ids: affectation[i] = m
    return modules, affectation


SOURCES = {'sec-st.json': 'pda-st-ste-secondaire.json', 'sec-ats.json': 'pda-ats-se-secondaire.json', 'sec-gcu.json': 'precision-gcu-secondaire.json',
           'sec-h20.json': 'precision-h20-secondaire.json', 'sec-mc.json': 'precision-mc4-secondaire.json', 'sec-edf.json': 'programme-edf-secondaire.json'}


def charger_complets(src, fichier):
    """Retrouve les savoirs complets (section et chemin entiers) dans donnees/ ; None si la discipline n'en a pas (HQC, CCQ)."""
    ordre, code = fichier[:-5].split('-', 1)
    nom = SOURCES.get(fichier) or f"pda-{code}-{'primaire' if ordre == 'pri' else 'secondaire'}.json"
    chemin = os.path.join(src, nom)
    if not os.path.exists(chemin): return None
    return json.load(open(chemin, encoding='utf-8')).get('savoirs')


def main(src, cat):
    os.makedirs(os.path.join(cat, 'modules'), exist_ok=True)
    index = json.load(open(os.path.join(cat, 'index.json'), encoding='utf-8'))
    bilan = []
    for e in index['disciplines']:
        libelles = {}
        d = json.load(open(os.path.join(cat, e['fichier']), encoding='utf-8'))
        ids = [s['id'] for s in d['savoirs']]
        sortie = os.path.join(cat, 'modules', e['fichier'])
        redige = os.path.join(src, '..', 'gemini', 'resultats', 'modules', e['fichier'])
        if os.path.exists(redige):
            m = json.load(open(redige, encoding='utf-8')); modules, aff, source = m['modules'], m['affectation'], 'rédigé (Gemini)'
            libelles = m.get('libelles', {})
        elif (e['ordre'], e['code']) in REGLES:
            regle, defs = REGLES[(e['ordre'], e['code'])]
            complets = {s['id']: s for s in charger_complets(src, e['fichier'])}
            aff = {i: regle(complets[i]) for i in ids}
            modules = [{'id': k, 'titre': t, 'description': dsc} for k, t, dsc in defs if k in set(aff.values())]
            source = 'rédigé'
        elif e['code'] == 'HQC':
            # un module par période ; les thèmes du programme restent visibles au niveau des savoirs
            h = json.load(open(os.path.join(src, 'programme-hqc-secondaire.json'), encoding='utf-8'))
            modules = [{'id': p['id'], 'titre': p['titre'], 'description': p['bornes'] + ' · ' + ', '.join(th['theme'] for th in p['themes'][:4]) + ('…' if len(p['themes']) > 4 else '')} for p in h['periodes']]
            aff = {s['id']: s['id'].split('-T')[0] for s in d['savoirs']}
            source = 'rédigé (périodes du programme)'
        else:
            complets = charger_complets(src, e['fichier'])
            par_id = {s['id']: s for s in (complets or [])}
            sv = [par_id.get(s['id'], {'id': s['id'], 'competence': s['g'], 'chemin': [s['s']]}) for s in d['savoirs']]
            modules, aff = modules_auto(sv); source = 'automatique'
        manquants = [i for i in ids if i not in aff]
        if manquants: raise SystemExit(f"{e['fichier']} : {len(manquants)} savoirs sans module")
        json.dump({'source': source, 'modules': modules, 'affectation': aff, **({'libelles': libelles} if libelles else {})}, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        bilan.append((e['ordre'][:4], e['code'], len(modules), source))
    for b in bilan: print('  {} {:<5} {:>3} modules · {}'.format(*b))


if __name__ == '__main__':
    main(*sys.argv[1:3])
