"""Extraction de la Progression des apprentissages en Culture et citoyenneté québécoise (2024).

Deux parties, au primaire comme au secondaire :
1. Indicateurs de progression (et autres tableaux à crochets) : par cycle, ✓ = visé, ––– = pas encore.
   Les tableaux sont découpés par les traits de chaque colonne : composante | énoncé (›) | précision (–) | cycles.
2. Répartition des éléments de contenu par année : thèmes, orientations, concepts ou sous-thèmes,
   éléments de contenu (☑) et notions et exemples associés (›).
Tout est du texte dans ce document (pas de symboles en image).
Usage : python3 -I extraire_ccq.py source.pdf primaire|secondaire sortie.json
"""
import json, re, sys, collections
import pdfplumber

COCHE = re.compile(r'^[✓✔]')
TRAIT = re.compile(r'^[–—-]{2,}$')


def nettoyer(t):
    t = re.sub(r'[️]', '', t or '')
    t = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '-', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def segments(page):
    """Traits horizontaux, regroupés par colonne (x0, x1 arrondis)."""
    segs = [(l['top'], l['x0'], l['x1']) for l in page.lines if abs(l['top'] - l['bottom']) < 1 and l['x1'] - l['x0'] > 30]
    segs += [(r['top'], r['x0'], r['x1']) for r in page.rects if r['height'] < 1.5 and r['width'] > 30]
    return segs


def tableau_a_crochets(page, num, titre_page):
    mots = page.extract_words(keep_blank_chars=False)
    entetes = [(w, mots[i - 1]) for i, w in enumerate(mots) if w['text'] == 'CYCLE' and i and re.match(r'^\d', mots[i - 1]['text'])]
    if not entetes:
        return []
    cycles = sorted(((w['x1'] + p['x0']) / 2, re.match(r'\d', p['text']).group(0)) for w, p in entetes)
    haut_entete = max(w['bottom'] for w, _ in entetes)
    marques = [w for w in mots if (COCHE.match(w['text']) or TRAIT.match(w['text'])) and w['top'] > haut_entete
               and min(abs((w['x0'] + w['x1']) / 2 - c) for c, _ in cycles) < 25]
    if not marques:
        return []
    segs = [s for s in segments(page) if s[0] > haut_entete - 2]
    gauches = collections.Counter(round(x0) for _, x0, _ in segs)
    # début de la première colonne de cycle : le trait le plus à gauche qui passe sous le premier cycle
    x_cycles = min((x0 for _, x0, x1 in segs if x0 < cycles[0][0] < x1 and x1 - x0 < 150), default=cycles[0][0] - 30)
    lefts = sorted(x for x, n in gauches.items() if n >= 2 and x < x_cycles - 10)
    lefts = [x for k, x in enumerate(lefts) if not k or x - lefts[k - 1] > 6]
    zones = [(a, b) for a, b in zip(lefts, lefts[1:] + [x_cycles])]
    def traits(x_gauche):
        return sorted({s[0] for s in segs if abs(s[1] - x_gauche) < 4})
    traits_zone = [traits(a) for a, _ in zones]
    traits_cycle = sorted({s[0] for s in segs if s[1] >= x_cycles - 4})
    # titre : la ligne de texte juste au-dessus du tableau
    haut_tab = min((s[0] for s in segments(page) if s[0] > haut_entete - 40), default=haut_entete) if False else haut_entete
    dessus = [w for w in mots if w['bottom'] < min(w2['top'] for w2, _ in entetes) - 2 and w['top'] > min(w2['top'] for w2, _ in entetes) - 45]
    titre = titre_page
    if dessus:
        y = max(w['top'] for w in dessus)
        ligne = sorted((w for w in dessus if abs(w['top'] - y) < 3), key=lambda w: w['x0'])
        cand = nettoyer(' '.join(w['text'] for w in ligne))
        if cand and 'CYCLE' not in cand and 'APPREND' not in cand:
            titre = cand
        elif titre_page:
            titre = titre_page
    sortie = []
    bas_marques = max(w['bottom'] for w in marques)
    fond = [y for y in traits_cycle if y > bas_marques - 1]
    bornes = [haut_entete] + [y for y in traits_cycle if haut_entete + 2 < y <= bas_marques] + [min(fond) if fond else bas_marques + 6]
    for rt, rb in zip(bornes, bornes[1:]):
        ws = [w for w in marques if rt - 1 <= (w['top'] + w['bottom']) / 2 <= rb + 1]
        if not ws:
            continue
        cy = (rt + rb) / 2
        valeurs = {}
        for w in ws:
            cx = (w['x0'] + w['x1']) / 2
            valeurs[min(cycles, key=lambda c: abs(c[0] - cx))[1]] = bool(COCHE.match(w['text']))
        cellules = []
        for (a, z), tr in zip(zones, traits_zone):
            dessus = [y for y in tr if y <= cy]
            dessous = [y for y in tr if y > cy]
            cellules.append((a, z, max(dessus) if dessus else rt, min(dessous) if dessous else rb))
        textes = []
        k = 0
        while k < len(cellules):
            a, z, t_, b_ = cellules[k]
            fin, k2 = z, k + 1
            # une cellule sans trait à sa droite s'étend (ex. énoncé sans précision)
            while k2 < len(cellules):
                a2, z2, t2, b2 = cellules[k2]
                suite = nettoyer(page.crop((a2 + 1, t2 + 0.5, z2 - 1, b2 - 0.5)).extract_text())
                if suite and (re.match(r'^[–−…•]', suite) or (t2, b2) != (t_, b_) and (b2 - t2) < (b_ - t_) - 2):
                    break   # vraie sous-cellule (précision), pas la suite du texte
                fin, k2 = z2, k2 + 1
            textes.append(re.sub(r'^[›–•]\s*', '', nettoyer(page.crop((a + 1, t_ + 0.5, fin - 1, b_ - 0.5)).extract_text())))
            k = k2
        sortie.append({'tableau': titre, 'cellules': [x for x in textes if x], 'cycles': dict(sorted(valeurs.items())), 'page': num})
    return sortie


def titre_tableau(page):
    for l in (page.extract_text() or '').split('\n')[:3]:
        l = l.strip()
        if l.startswith('Indicateurs de progression') or (l and not l.isupper() and len(l) < 90 and 'CYCLE' not in l):
            return nettoyer(l)
    return ''


def gras(ligne):
    return sum('Bd' in c['fontname'] or 'Bold' in c['fontname'] for c in ligne['chars']) > len(ligne['chars']) / 2


def page_contenu(page):
    """Page « Éléments de contenu » : colonnes de concepts (secondaire) ou de sous-thèmes (primaire)."""
    lignes = page.extract_text_lines()
    banniere = [l for l in lignes if 'Notions et exemples associés' in l['text']]
    if not banniere:
        return None
    haut = banniere[0]['bottom'] + 2
    bas = min((l['top'] for l in lignes if l['text'].startswith('Programme de formation')), default=page.height - 40) - 2
    puces = collections.Counter(round(c['x0'] / 3) * 3 for c in page.chars if c['text'] == '›' and c['top'] > haut)
    starts = sorted(x for x, n in puces.items() if n >= 1)
    starts = [x for k, x in enumerate(starts) if not k or x - starts[k - 1] > 40]
    colonnes = [(x - 4, (starts[k + 1] - 4) if k + 1 < len(starts) else page.width - 30) for k, x in enumerate(starts)]
    # en-têtes de colonnes : mots entre « CONCEPTS PRINCIPAUX » (ou l'année) et la bannière, au-dessus des colonnes
    debut_entete = max((l['bottom'] for l in lignes if re.search(r'CONCEPTS PRINCIPAUX|ANNÉE$', l['text']) and l['top'] < haut), default=haut - 80)
    fin_entete = min((l['top'] for l in lignes if re.search(r'(Concepts particuliers|Éléments de contenu obligatoires)', l['text'])), default=haut - 30)
    mots = [w for w in page.extract_words() if debut_entete < w['top'] < fin_entete - 1]
    entetes = ['' for _ in colonnes]
    largeur = (colonnes[-1][1] - colonnes[0][0]) / len(colonnes) if colonnes else 1
    for w in sorted(mots, key=lambda w: (round(w['top']), w['x0'])):
        cx = (w['x0'] + w['x1']) / 2
        k = min(range(len(colonnes)), key=lambda k: abs((colonnes[k][0] + colonnes[k][1]) / 2 - cx))
        entetes[k] = (entetes[k] + ' ' + w['text']).strip()
    sortie = []
    for (a, b), entete in zip(colonnes, entetes):
        elements, courant, mode = [], None, None
        for l in page.crop((a, haut, b, bas)).extract_text_lines():
            txt = re.sub(r'^[\ue000-\uf8ff☑\s]+', '', l['text']).strip()   # case à cocher (glyphe privé)
            if not txt:
                continue
            if txt.startswith('›'):
                if courant is None:
                    courant = {'element': '', 'notions': ''}; elements.append(courant)
                courant['notions'] = (courant['notions'] + ' ' + txt[1:].strip()).strip()
                mode = 'notions'
            elif txt.startswith('ES :'):
                if courant is None:
                    courant = {'element': '', 'notions': ''}; elements.append(courant)
                courant.setdefault('education_sexualite', [])
                courant['education_sexualite'].append(txt[4:].strip())
                mode = 'es'
            elif gras(l) and mode != 'titre':
                courant = {'element': txt, 'notions': ''}; elements.append(courant)
                mode = 'titre'
            elif mode == 'titre' and gras(l):
                courant['element'] += ' ' + txt
            elif mode == 'es':
                courant['education_sexualite'][-1] += ' ' + txt
            elif courant is not None:
                courant['notions'] = (courant['notions'] + ' ' + txt).strip()
        for e in elements:
            e['element'] = nettoyer(e['element'])
            e['notions'] = nettoyer(e['notions'])
        sortie.append({'colonne': nettoyer(entete), 'elements': elements})
    return sortie


def extraire_contenus(src, ordre):
    pdf = pdfplumber.open(src)
    blocs, annee, theme = [], None, None
    for num, page in enumerate(pdf.pages, 1):
        lignes = [l['text'].strip() for l in page.extract_text_lines()]
        haut = ' | '.join(lignes[:6])
        m = re.search(r'(\d)(?:re|e) (SECONDAIRE|ANNÉE)', haut)
        if m:
            annee = m.group(1)
        if ordre == 'secondaire' and len(lignes) > 1 and m:
            k = next((i for i, l in enumerate(lignes[:4]) if re.search(r'SECONDAIRE', l)), 0)
            theme = lignes[k + 1].title() if k + 1 < len(lignes) else theme
            theme = re.sub(r'\bEt\b', 'et', theme)
        if re.search(r'ORIENTATIONS', haut):
            corps = [l for l in lignes if not re.search(r'ORIENTATIONS|SECONDAIRE$|CYCLE DU PRIMAIRE|^ÉLÉMENTS DE CONTENU|^Programme de formation', l)]
            if ordre == 'secondaire':
                corps = corps[1:] if corps and corps[0].isupper() else corps
            blocs.append({'annee': annee, 'theme': theme, 'type': 'orientations', 'texte': nettoyer(' '.join(corps)), 'page': num})
            continue
        colonnes = page_contenu(page)
        if colonnes:
            blocs.append({'annee': annee, 'theme': theme, 'type': 'contenus', 'colonnes': colonnes, 'page': num})
    return blocs


def extraire(src, ordre):
    pdf = pdfplumber.open(src)
    tableaux = []
    for num, page in enumerate(pdf.pages, 1):
        tableaux += tableau_a_crochets(page, num, titre_tableau(page))
    return tableaux


if __name__ == '__main__':
    src, ordre, sortie = sys.argv[1:4]
    lettre = 'P' if ordre == 'primaire' else 'S'
    tableaux = extraire(src, ordre)
    cycles = sorted({c for r in tableaux for c in r['cycles']})
    indicateurs, autres = [], []
    for r in tableaux:
        c = r['cellules']
        if r['tableau'].startswith('Indicateurs de progression'):
            comp = re.sub(r'^Indicateurs de progression de la compétence\s*', '', r['tableau']).strip()
            indicateurs.append({'competence': comp, 'composante': c[0] if c else '', 'enonce': c[1] if len(c) > 1 else '',
                                **({'precision': ' — '.join(c[2:])} if len(c) > 2 else {}),
                                'cycles': r['cycles'], 'page': r['page']})
        else:
            autres.append({'tableau': r['tableau'], 'element': ' — '.join(c), 'cycles': r['cycles'], 'page': r['page']})
    for k, s in enumerate(indicateurs, 1):
        s['id'] = f'CCQ{lettre}-IND-{k:03d}'
    for k, s in enumerate(autres, 1):
        s['id'] = f'CCQ{lettre}-ELC-{k:03d}'
    blocs = extraire_contenus(src, ordre)
    contenus, n = [], 0
    for b in blocs:
        theme = (b['theme'] or '')
        theme = theme[:1] + theme[1:].lower() if theme else None
        if b['type'] == 'orientations':
            contenus.append({'annee': b['annee'], **({'theme': theme} if theme else {}), 'orientations': b['texte'], 'colonnes': [], 'page': b['page']})
            continue
        cible = next((c for c in contenus if c['annee'] == b['annee'] and c.get('theme') == theme and not c['colonnes']), None)
        if cible is None:
            cible = {'annee': b['annee'], **({'theme': theme} if theme else {}), 'colonnes': [], 'page': b['page']}
            contenus.append(cible)
        for col in b['colonnes']:
            elts = []
            for e in col['elements']:
                n += 1
                elts.append({'id': f'CCQ{lettre}-CON-{n:03d}', **({'element': e['element']} if e['element'] else {'notions_du_concept': True}),
                             'notions': e['notions'], **({'education_sexualite': e['education_sexualite']} if e.get('education_sexualite') else {})})
            cible['colonnes'].append({('sous_theme' if ordre == 'primaire' else 'concept_principal'): col['colonne'], 'elements': elts})
    out = {'discipline': 'Culture et citoyenneté québécoise', 'code_discipline': 'CCQ', 'ordre': ordre,
           'source': src.split('/')[-1], 'version': '2024', 'cycles': cycles,
           'legende': {'cycles': 'true : visé à ce cycle (crochet) ; false : pas encore (trait)',
                       'contenus': 'Par année : orientations, puis éléments de contenu obligatoires et notions et exemples associés',
                       **({'education_sexualite': 'Éléments de contenu spécifiques (obligatoires) en éducation à la sexualité'} if ordre == 'primaire' else {})},
           'bilan': {'indicateurs': len(indicateurs), 'elements_lies_competence': len(autres), 'annees': len({c['annee'] for c in contenus}),
                     'elements_de_contenu': n},
           'indicateurs': indicateurs, 'elements_lies_a_la_competence': autres, 'contenus': contenus}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False))
