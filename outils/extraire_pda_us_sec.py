"""Extraction des PDA d'univers social au 1er cycle du secondaire.

- Géographie : une seule colonne « 1re ou 2e » ;
- Histoire et éducation à la citoyenneté : deux colonnes, 1re et 2e, séparées par un pointillé.
Les colonnes sont repérées par le trait vertical de gauche et le bord droit du tableau ;
les cellules sont lues par pixels comme en mathématique (voir extraire_pda_math_sec.py).
Usage : python3 -I extraire_pda_us_sec.py source.pdf GEO|HEC sortie.json
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M

NOMS = {'GEO': 'Géographie (1er cycle)', 'HEC': 'Histoire et éducation à la citoyenneté (1er cycle)'}


def colonnes(page):
    gauche = [r['x0'] for r in page.rects if r['width'] < 2.5 and r['height'] > 8 and 470 < r['x0'] < 500]
    gauche += [l['x0'] for l in page.lines if abs(l['x0'] - l['x1']) < 1 and 470 < l['x0'] < 500]
    if not gauche:
        return None
    x0 = collections.Counter(round(x, 1) for x in gauche).most_common(1)[0][0]
    bords = [r['x1'] for r in page.rects if r['height'] < 2.5 and x0 + 30 < r['x1'] < x0 + 70]
    x1 = collections.Counter(round(b, 1) for b in bords).most_common(1)[0][0] if bords else x0 + 49
    if len(M.ANNEES) == 1:
        return [(x0, x1)]
    milieu = (x0 + x1) / 2
    return [(x0, milieu), (milieu, x1)]


def sous_tableaux(src, savoirs):
    """Rangées découpées en sous-colonnes (ex. « Révolution américaine | Révolution française ») :
    les bornes viennent des traits verticaux de la rangée ; le texte est relu zone par zone.
    La rangée d'en-tête est retirée ; ses intitulés nomment les zones (repris à la page suivante)."""
    import pdfplumber
    pdf = pdfplumber.open(src)
    garde, noms = [], None
    for s in savoirs:
        page = pdf.pages[s['page'] - 1]
        t, b = s['_bande']
        x_col = s['_x_col']
        if re.fullmatch(r'(Révolution (américaine|française)\s*){2}', s['texte']):
            noms = ['Révolution américaine', 'Révolution française']
            continue
        traits = sorted({round(r['x0'], 1) for r in page.rects if r['width'] < 2.5 and r['top'] < b - 2 and r['bottom'] > t + 2 and 100 < r['x0'] < x_col - 5}
                        | {round(l['x0'], 1) for l in page.lines if abs(l['x0'] - l['x1']) < 1 and l['top'] < b - 2 and l['bottom'] > t + 2 and 100 < l['x0'] < x_col - 5})
        if not traits or not noms:
            garde.append(s); continue
        bornes = [0] + list(traits) + [x_col]
        zones = [re.sub(r'\s+', ' ', page.crop((a + 0.5, t, z - 0.5, b)).extract_text() or '').strip() for a, z in zip(bornes, bornes[1:])]
        enonce, valeurs = zones[0], [v for v in zones[1:]]
        if len(valeurs) == 1:
            s['texte'] = f'{enonce} : {valeurs[0]}'   # cellule fusionnée : vaut pour les deux
        else:
            s['texte'] = enonce + ' : ' + ' ; '.join(f'{n} : {v}' for n, v in zip(noms, valeurs) if v)
        s['a_verifier'], s['note'] = False, 'Sous-tableau relu par zones.'
        garde.append(s)
    savoirs[:] = garde


if __name__ == '__main__':
    src, code, sortie = sys.argv[1:4]
    M.ANNEES[:] = ['1-2'] if code == 'GEO' else ['1', '2']
    M.COLONNES_SEQUENCES = ()
    M.SEPARER_FIN = True
    M.colonnes = colonnes
    savoirs, sans_colonnes = M.extraire(src)
    sous_tableaux(src, savoirs)
    for s in savoirs:
        s['texte'] = re.sub(r'\^(e|er|re|es|ers|res)\b', r'\1', s['texte'])   # XV^e siècle -> XVe siècle
        s['texte'] = re.sub(r'(?<=\w)- (?=\w)', '-', s['texte'])   # mot composé coupé en fin de ligne (« Saint- Laurent »)
        s['chemin'] = [re.sub(r'\^(e|er|re|es|ers|res)\b', r'\1', c) for c in s['chemin']]
        if s.get('section'):
            s['section'] = re.sub(r'\s+Année(?=\s|$)', '', s['section']).strip()
            if s['section'].isupper():   # titres en capitales : en minuscules, sauf l'initiale
                m = re.match(r'^([A-D]\.\s+)?(.*)$', s['section'])
                s['section'] = (m.group(1) or '') + m.group(2)[:1] + m.group(2)[1:].lower()
        if s['note'].startswith('Formule') and '^' not in s['texte'] and '=' not in s['texte']:
            s['a_verifier'], s['note'] = False, ''
        s['texte'] = re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', s['texte'])
        s['chemin'] = [re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', c) for c in s['chemin']]
    compteur = collections.Counter()
    for s in savoirs:
        cle = re.sub(r'[^A-Z]', '', (s['champ'] or 'XXX').upper().replace('É', 'E').replace('È', 'E'))[:3]
        compteur[cle] += 1
        s['id'] = f'{code}-{cle}-{compteur[cle]:03d}'
    out = {'discipline': NOMS[code], 'code_discipline': code, 'ordre': 'secondaire',
           'source': src.split('/')[-1], 'annees': M.ANNEES,
           **({'legende': {'1-2': 'Une seule colonne dans le document : 1re ou 2e secondaire, au choix de l’école'}} if code == 'GEO' else {}),
           'pages_sans_colonnes_reperees': sans_colonnes,
           'bilan': {'nombre_savoirs': len(savoirs), 'a_verifier': sum(s['a_verifier'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'section', 'chemin', 'texte', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False), 'pages sans colonnes :', sans_colonnes, dict(M.CONTROLE))
