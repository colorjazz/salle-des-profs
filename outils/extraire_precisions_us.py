"""Extraction des « Précision des apprentissages » d'univers social au 2e cycle du secondaire
(géographie culturelle, histoire du 20e siècle, monde contemporain 2 et 4 unités).

Ces documents n'ont pas de progression par année : ce sont des listes hiérarchisées.
Thème (titre de page) > 1. section > 1.1. sous-section > a. énoncé. Chaque énoncé est un savoir.
Usage : python3 -I extraire_precisions_us.py source.pdf CODE "Discipline" "5e" sortie.json
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M
import pdfplumber


def titre_page(page):
    gros = [c for c in page.chars if c['size'] >= 12 and c['top'] <= 110 and c['text'].strip()]
    if not gros:
        return ''
    derniere = max(round(c['top']) for c in gros)
    ligne = sorted((c for c in gros if abs(round(c['top']) - derniere) <= 2), key=lambda c: c['x0'])
    t = ''
    for k, c in enumerate(ligne):
        if k and c['x0'] - ligne[k - 1]['x1'] > 0.2 * c['size']:
            t += ' '
        t += c['text']
    return t.strip()


def extraire(src):
    pdf = pdfplumber.open(src)
    theme, pile, savoirs = None, {}, []
    for num, page in enumerate(pdf.pages, 1):
        t = titre_page(page)
        if t:
            theme, pile = t, {}
        rangs = M.lignes_texte(page, page.width - 20, 30, page.height - 25)
        rangs = [r for r in rangs if not re.fullmatch(r'\d{1,3}', r['texte'])]   # numéro de page
        rangs = [r for r in rangs if r['top'] > 60 or not t]   # sous le titre
        elements, debut = [], False
        for r in rangs:
            n = None if r['petit'] else M.niveau(r['texte'])
            if n is not None:
                debut = True
                elements.append({'niveau': n, 'lignes': [r]})
            elif debut and elements and not r['petit'] and r['x0'] > elements[-1]['lignes'][0]['x0'] - 2 \
                    and r['top'] - elements[-1]['lignes'][-1]['bottom'] < 8:
                elements[-1]['lignes'].append(r)   # suite de l'énoncé
            elif debut and r['petit'] and elements and re.match(r'^Note\b', r['texte']):
                elements[-1].setdefault('notes', []).append(r)
        for e in elements:
            texte = re.sub(r'\s+', ' ', ' '.join(l['texte'] for l in e['lignes'])).strip()
            texte = re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', texte)
            texte = re.sub(r'(?<=\w)- (?=\w)', '-', texte)   # mot composé coupé en fin de ligne (« main- d’œuvre »)
            texte = re.sub(r'\^(e|er|re|es|ers|res)\b', r'\1', texte)
            n = e['niveau']
            if n < 3:
                pile = {k: v for k, v in pile.items() if k < n}
                pile[n] = texte
                continue
            savoirs.append({'theme': theme, 'chemin': [pile[k] for k in sorted(pile) if k < n],
                            'texte': texte, 'page': num,
                            **({'note_pda': ' '.join(l['texte'] for l in e['notes'])} if e.get('notes') else {})})
    return savoirs


if __name__ == '__main__':
    src, code, disc, annee, sortie = sys.argv[1:6]
    savoirs = extraire(src)
    # clé de thème : 3 lettres du premier mot significatif ; en cas de doublon, celles du dernier
    vides = {'aire', 'culturelle', 'les', 'la', 'le', 'un', 'une', 'du', 'de', 'des', 'au', 'et'}
    def mots(theme):
        return [m for m in re.split(r"[\s’'-]+", theme or 'XXX') if m.lower() not in vides and m.lower() != 'l']
    def lettres(m):
        return re.sub(r'[^A-Z]', '', m.upper().replace('É', 'E').replace('È', 'E'))[:3]
    themes = list(dict.fromkeys(s['theme'] for s in savoirs))
    cles = {th: lettres(mots(th)[0]) for th in themes}
    for th in themes:
        if list(cles.values()).count(cles[th]) > 1:
            cles[th] = lettres(mots(th)[-1])
    compteur = collections.Counter()
    for s in savoirs:
        cle = cles[s['theme']]
        compteur[cle] += 1
        s['id'] = f'{code}-{cle}-{compteur[cle]:03d}'
    out = {'discipline': disc, 'code_discipline': code, 'ordre': 'secondaire', 'annee': annee,
           'source': src.split('/')[-1],
           'type': 'Précision des apprentissages : liste d’énoncés, sans progression par année',
           'themes': list(dict.fromkeys(s['theme'] for s in savoirs)),
           'bilan': {'nombre_savoirs': len(savoirs), 'par_theme': dict(collections.Counter(s['theme'] for s in savoirs))},
           'savoirs': [{k: s[k] for k in ('id', 'theme', 'chemin', 'texte', 'page', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False))
