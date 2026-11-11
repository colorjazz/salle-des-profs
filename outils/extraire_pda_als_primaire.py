"""Extraction de la PDA d'anglais, langue seconde, au primaire.

Deux tableaux côte à côte sur chaque page :
- à gauche, le 1er cycle (langage contextuel) : colonnes 1re et 2e, souvent fusionnées en une
  seule cellule « 1er cycle » (flèche avec appel de note ¹) : on note alors la progression `1-2` ;
- à droite, les 2e et 3e cycles (langage fonctionnel, stratégies, etc.) : colonnes 3e à 6e.
Les cellules sont des aplats de couleur (pas de traits verticaux) : la grille est lue d'après les
rectangles de fond. Lecture des symboles par pixels comme en mathématique (extraire_pda_math_sec.py).
Usage : python3 -I extraire_pda_als_primaire.py source.pdf sortie.json
"""
import json, os, re, sys, collections, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M


def grappes(xs, ecart=2.5):
    g = []
    for x in sorted(xs):
        if g and x - g[-1][-1] < ecart:
            g[-1].append(x)
        else:
            g.append([x])
    return [(sum(v) / len(v), len(v)) for v in g]


def gauche(page):
    """Début de la colonne 1er cycle (x ≈ 231 à 239 selon la page)."""
    xs = [r['x0'] for r in page.rects if r['width'] < 40 and r['height'] > 5 and 220 < r['x0'] < 245]
    g = [x for x, n in grappes(xs) if n >= 2]
    return min(g) if g else None


def droite(page):
    xs = [r['x0'] for r in page.rects if r['width'] < 40 and r['height'] > 5 and 455 < r['x0'] < 530]
    g = [x for x, n in grappes(xs) if n >= 2]
    if len(g) < 4:
        return None
    g = g[:4]
    return [(a, b) for a, b in zip(g, g[1:])] + [(g[3], g[3] + (g[3] - g[0]) / 3)]


VERBE = re.compile(r'^[A-ZÉÈ][a-zéèêûô’\']+(?:er|ir|re)\b|^S’|^Se ')


def scinder(texte):
    """Coupe avant un verbe à l'infinitif en majuscule, hors des parenthèses
    (« … flashcards) Utiliser du vocabulaire… »)."""
    morceaux, debut, prof = [], 0, 0
    for m in re.finditer(r'[()]|\s(?=[A-ZÉÈ][a-zéèêûô]+(?:er|ir|re)\b)', texte):
        if m.group(0) == '(':
            prof += 1
        elif m.group(0) == ')':
            prof = max(0, prof - 1)
        elif prof == 0 and m.start() > debut + 15:
            morceaux.append(texte[debut:m.start()].strip()); debut = m.start()
    morceaux.append(texte[debut:].strip())
    return [x for x in morceaux if x]


def bords(page, garder):
    """Bords haut et bas des rectangles de cellule (cellules à bordure, sans traits séparés)."""
    ys = set()
    for r in page.rects:
        if r['height'] > 4 and garder(r):
            ys.add(round(r['top'], 1)); ys.add(round(r['bottom'], 1))
    return sorted(ys)


def passe(src, cote):
    importlib_reload()
    M.COLONNES_SEQUENCES = ()
    M.SEPARER_FIN = True
    M.RUBRIQUES = True
    M.HERITER_HAUT_DE_PAGE = True
    M.LETTRES_TAILLE_MIN = 8          # l'appel de note « ¹ » près de la flèche n'est pas du texte de cellule
    if cote == 'droite':
        M.ANNEES[:] = ['3', '4', '5', '6']
        M.colonnes = droite
        M.TEXTE_X_MIN = lambda page: (gauche(page) or 236) + 34
        M.HORIZ_FILTRE = lambda page, x0, x1: x1 > (gauche(page) or 236) + 40
        M.HORIZ_EXTRA = lambda page: bords(page, lambda r: r['x0'] > (gauche(page) or 236) + 30 and r['x0'] < 300 and r['x1'] > 400)
    else:
        M.ANNEES[:] = ['1', '2']
        M.colonnes = lambda page: (lambda g: [(g, g + 18), (g + 18, g + 36)] if g else None)(gauche(page))
        M.TEXTE_X_MIN = 0
        # rangées : cellules de la colonne du 1er cycle (une flèche peut couvrir plusieurs énoncés)
        M.HORIZ_FILTRE = lambda page, x0, x1: False
        M.HORIZ_EXTRA = lambda page: bords(page, lambda r: abs(r['x0'] - (gauche(page) or 236)) < 3 and r['width'] > 30)
        lire = M.valeur
        def valeur(rendu, cellule_x, bande):
            (x0, x1), (t, b) = cellule_x, bande
            g = gauche_de(rendu)
            if g is not None:
                tache = rendu.tache(g + 2, g + 34, t + 2.5, b - 2.5, seuil=140)
                centree = tache and abs((tache[0] + tache[2]) / 2 - (g + 18)) < 6
                if centree:   # symbole centré sur la cellule fusionnée du 1er cycle
                    v = lire(rendu, (g, g + 36), bande)
                    return ('fusion:' + v) if v and abs(x0 - g) < 1 else None
            return lire(rendu, cellule_x, bande)
        M.valeur = valeur
    savoirs, _ = M.extraire(src)
    return savoirs


_GAUCHES = {}


def gauche_de(rendu):
    return _GAUCHES.get(rendu.num)


def importlib_reload():
    import importlib
    importlib.reload(M)


if __name__ == '__main__':
    src, sortie = sys.argv[1:3]
    import pdfplumber
    pdf = pdfplumber.open(src)
    for n, p in enumerate(pdf.pages, 1):
        _GAUCHES[n] = gauche(p)
    resultats = {}
    for cote in ('gauche', 'droite'):
        savoirs = passe(src, cote)
        for s in savoirs:
            if s['note'].startswith('Ligne sans marqueur'):
                s['a_verifier'], s['note'] = False, ''
            s['texte'] = re.sub(r'(?<=\w)- (?=\w)', '-', re.sub(r'\^(e|er|re|es)\b', r'\1', s['texte']))
            s['texte'] = re.sub(r'^\^?1\s+', '', s['texte'])
            p = s['progression']
            if cote == 'gauche':
                if isinstance(p.get('1'), str) and p['1'].startswith('fusion:'):
                    s['progression'] = {'1-2': p['1'][7:] or None}
            s['cycle'] = '1er cycle' if cote == 'gauche' else '2e et 3e cycles'
            s.pop('section', None)
            r = s.get('rubrique', '')
            m = re.match(r"^((?:[A-Z]\.?—)?[A-ZÉÈÀÇ’' —-]{4,}?)\s+(?=[A-ZÉÈ][a-zéèê])", r)
            if m:   # intitulé en capitales (« LANGAGE CONTEXTUEL », « B—STRATÉGIES… ») : section
                s['section'], s['rubrique'] = m.group(1).strip(), r[m.end():].strip()
        resultats[cote] = savoirs
    # en haut de page, la fin d'un énoncé commencé à la page précédente (parenthèse ouverte, minuscule) s'y rattache
    for cote in resultats:
        garde, page_vue = [], set()
        for s in resultats[cote]:
            premier = s['page'] not in page_vue
            page_vue.add(s['page'])
            ouvert = garde and garde[-1]['texte'].count('(') > garde[-1]['texte'].count(')')
            if premier and garde and (ouvert or s['texte'][:1].islower()):
                garde[-1]['texte'] += ' ' + s['texte']
                continue
            garde.append(s)
        resultats[cote] = garde
    # plusieurs énoncés dans une même cellule : on les sépare (même progression)
    for cote in resultats:
        separes = []
        for s in resultats[cote]:
            for morceau in scinder(s['texte']):
                separes.append(dict(s, texte=morceau))
        resultats[cote] = separes
    savoirs = resultats['gauche'] + resultats['droite']
    savoirs = [s for s in savoirs if not re.match(r'^(L’élève (apprend|le fait|réutilise))', s['texte'])]
    vides = {'le', 'la', 'les', 'de', 'des', 'du', 'et', 'l', 'd', 'catégorie'}
    compteur = collections.Counter()
    for s in savoirs:
        m = re.match(r'^Catégorie (\d)', s['champ'] or '')
        cle = f'C{m.group(1)}' if m else 'XX'
        cle += 'G' if s['cycle'] == '1er cycle' else 'D'
        compteur[cle] += 1
        s['id'] = f'ALS-{cle}-{compteur[cle]:03d}'
    out = {'discipline': 'Anglais, langue seconde', 'code_discipline': 'ALS', 'ordre': 'primaire',
           'source': src.split('/')[-1], 'annees': ['1', '2', '3', '4', '5', '6'],
           'legende': {'1er cycle': 'Tableau de gauche (langage contextuel, etc.) : colonnes 1 et 2, ou `1-2` quand le document fusionne la cellule du cycle',
                       '2e et 3e cycles': 'Tableau de droite : colonnes 3 à 6',
                       'rubrique': 'Intitulé en gras qui regroupe les énoncés (ex. « Demande d’information »)'},
           'bilan': {'nombre_savoirs': len(savoirs), '1er_cycle': len(resultats['gauche']), '2e_3e_cycles': len(resultats['droite']),
                     'a_verifier': sum(s['a_verifier'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'cycle', 'section', 'chemin', 'rubrique', 'texte', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False))
