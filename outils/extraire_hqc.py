"""Extraction du programme d'Histoire du Québec et du Canada (3e et 4e secondaire) vers JSON.

Lit la structure du PDF : pages « Précision des connaissances » (thèmes en gras 10 pt, éléments « a. »,
deux colonnes), schémas de structure (concepts particuliers par période), textes de la réalité sociale.
Usage : python3 -I extraire_hqc.py programme.pdf cadre.pdf sortie.json
"""
import json, re, sys
import pdfplumber

COL = 390  # limite entre les deux colonnes (page de 792 pt, à l'italienne)
BAS = 540  # au-delà : pied de page

def lignes(page, colonne):
    mots = [w for w in page.extract_words(extra_attrs=['fontname', 'size'])
            if w['top'] < BAS and ((w['x0'] < COL) == (colonne == 'G'))
            and not (w['x0'] > 700 and re.fullmatch(r'\d+', w['text']))]  # numéro de page
    rang = {}
    for w in mots:
        rang.setdefault(round(w['top']), []).append(w)
    sortie = []
    for top in sorted(rang):
        ws = sorted(rang[top], key=lambda w: w['x0'])
        sortie.append({'top': top, 'x0': ws[0]['x0'], 'texte': ' '.join(w['text'] for w in ws),
                       'gras': 'Bold' in ws[0]['fontname'], 'taille': round(ws[0]['size'])})
    return sortie

def precision(pdf, i):
    """Thèmes et éléments d'une période, à partir de la page i (et de la suivante si elle continue)."""
    pages = [pdf.pages[i]]
    suiv = pdf.pages[i + 1].extract_text() or ''
    if 'Réalité sociale' not in suiv and 'Structure du programme' not in suiv and 'Annexe' not in suiv:
        pages.append(pdf.pages[i + 1])
    themes = []
    # l'en-tête (bornes et titre, 14 pt gras) peut déborder sur la colonne de droite : lu sur toute la largeur
    mots14 = sorted([w for w in pages[0].extract_words(extra_attrs=['fontname', 'size']) if round(w['size']) == 14 and 'Bold' in w['fontname']],
                    key=lambda w: (round(w['top']), w['x0']))
    entete = ' '.join(w['text'] for w in mots14)
    for p in pages:
        for col in ('G', 'D'):
            for l in lignes(p, col):
                t = l['texte']
                if l['taille'] == 14 and l['gras']:
                    continue
                if l['gras'] and l['taille'] == 10:
                    themes.append({'theme': t, 'elements': []}); continue
                m = re.match(r'^([a-z])\.\s+(.*)$', t)
                if m and themes:
                    themes[-1]['elements'].append({'lettre': m.group(1), 'texte': m.group(2)}); continue
                if themes and themes[-1]['elements'] and not l['gras'] and l['taille'] == 10:
                    prec = themes[-1]['elements'][-1]['texte']
                    themes[-1]['elements'][-1]['texte'] = prec + t if prec.endswith('-') else prec + ' ' + t  # ligne de suite
    return entete, themes

def texte_realite(pdf, debut, fin):
    """Texte officiel de la réalité sociale (pages debut..fin-1), colonne de gauche puis de droite."""
    parts = []
    for i in range(debut, fin):
        for col in ('G', 'D'):
            for l in lignes(pdf.pages[i], col):
                if l['taille'] == 10 and not l['gras'] and not re.fullmatch(r'\d+', l['texte']):
                    parts.append(l['texte'])
    t = ' '.join(parts)
    return re.sub(r'\s+', ' ', t.replace('- ', '-')).strip()

def concepts_par_periode(pdf):
    """Concepts particuliers, lus dans les deux schémas « Structure du programme » : chaque concept commence par une puce."""
    res = []
    for p in pdf.pages:
        txt = p.extract_text() or ''
        if 'Concepts communs' not in txt or 'particuliers' not in txt:
            continue
        rangs = {}
        for w in p.extract_words():
            rangs.setdefault(round(w['top']), []).append(w)
        colonnes = None
        for top in sorted(rangs):
            ws = sorted(rangs[top], key=lambda w: w['x0'])
            if not any(w['text'] == '\uf0a7' for w in ws):
                continue
            items, cur = [], None
            for w in ws:
                if w['text'] == '\uf0a7':
                    cur = []; items.append(cur)
                elif cur is not None:
                    cur.append(w['text'])
            if colonnes is None:
                colonnes = [[] for _ in items]
            for k, it in enumerate(items):
                colonnes[k].append(' '.join(it))
        res.extend(colonnes or [])
    return res

def pages_a_sauter(texte):
    return texte.lstrip().startswith('Précision des connaissances') or 'Concepts communs' in texte or 'Structure du programme' in texte

def main(prog, cadre, sortie):
    pdf = pdfplumber.open(prog)
    idx = [i for i, p in enumerate(pdf.pages) if (p.extract_text() or '').lstrip().startswith('Précision des connaissances')]
    periodes = []
    schema1 = next(k for k, p in enumerate(pdf.pages) if 'Concepts communs' in (p.extract_text() or '') and 'particuliers' in (p.extract_text() or ''))
    fin_prec = schema1
    for n, i in enumerate(idx, 1):
        entete, themes = precision(pdf, i)
        m = re.match(r'^(Des origines à 1608|De 1980 à nos jours|\d{4}-\d{4})\s+(.*)$', entete or '')
        bornes, titre = (m.group(1), m.group(2)) if m else (entete, '')
        # le texte de la réalité sociale : des pages qui suivent la période précédente (ou le schéma) jusqu'à la page de précision
        debut = fin_prec + 1
        while debut < i and pages_a_sauter(pdf.pages[debut].extract_text() or ''):
            debut += 1
        periodes.append({'id': f'HQC-P{n}', 'niveau': 'S3' if n <= 4 else 'S4', 'bornes': bornes, 'titre': titre,
                         'realite_sociale': texte_realite(pdf, debut, i), 'page': i + 1,
                         'themes': [{'id': f'HQC-P{n}-T{k:02d}', 'theme': t['theme'],
                                     'elements': [{'id': f'HQC-P{n}-T{k:02d}-{e["lettre"]}', 'texte': e['texte']} for e in t['elements']]}
                                    for k, t in enumerate(themes, 1)]})
        suiv = pdf.pages[i + 1].extract_text() or ''
        fin_prec = i + (1 if ('Réalité sociale' not in suiv and 'Structure du programme' not in suiv and 'Annexe' not in suiv) else 0)
    conc = concepts_par_periode(pdf)
    for p, c in zip(periodes, conc):
        p['concepts_particuliers'] = c
    data = {
        'discipline': 'Histoire du Québec et du Canada', 'code_discipline': 'HQC', 'ordre': 'secondaire', 'niveaux': ['S3', 'S4'],
        'source': {'programme': prog.split('/')[-1], 'cadre': cadre.split('/')[-1], 'date_version_programme': '2017'},
        'competences': [{'code': 'HQC-C1', 'nom': 'Caractériser une période de l’histoire du Québec et du Canada'},
                        {'code': 'HQC-C2', 'nom': 'Interpréter une réalité sociale'}],
        'concepts_communs': ['culture', 'économie', 'pouvoir', 'société', 'territoire'],
        'periodes': periodes,
    }
    # cadre d'évaluation
    ct = ' '.join((p.extract_text() or '') for p in pdfplumber.open(cadre).pages)
    ops = re.findall(r'•\s*([^•\n]+)', ct)
    data['cadre_evaluation'] = {
        'resultat': 'Un seul résultat disciplinaire pour les deux compétences (100 %)',
        'criteres': ['Maîtrise des connaissances présentées dans la section intitulée Contenu de formation',
                     'Utilisation appropriée de connaissances', 'Représentation cohérente d’une période de l’histoire du Québec et du Canada',
                     'Rigueur de l’interprétation'],
        'operations_intellectuelles': [o.strip() for o in ops],
        'note': 'L’utilisation et la production d’outils techniques (lignes du temps, cartes historiques) peuvent faire l’objet d’une rétroaction, mais ne comptent pas dans les résultats du bulletin.'}
    json.dump(data, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(len(periodes), 'périodes ;', sum(len(p['themes']) for p in periodes), 'thèmes ;',
          sum(len(t['elements']) for p in periodes for t in p['themes']), 'éléments ;', len(data['cadre_evaluation']['operations_intellectuelles']), 'opérations')

if __name__ == '__main__':
    main(*sys.argv[1:4])
