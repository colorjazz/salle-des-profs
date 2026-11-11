"""Recoupe une vérification visuelle (Gemini) de la PDA de français au secondaire avec une lecture des cellules par pixels.
Usage : python3 -I recouper_verification_fra_sec.py PDA.pdf verification_gemini.json sortie.json
Les désaccords sont à trancher en regardant la page (voir README)."""
import sys, json, re, unicodedata, collections
sys.path.insert(0, '/home/user/salle-des-profs/outils')
import extraire_pda_math_sec as M
import pdfplumber
M.LETTRES_TAILLE_MIN = 99   # efface tout le texte de l'image : seuls les symboles et les cases restent
src, gem = sys.argv[1], sys.argv[2]
pdf = pdfplumber.open(src)
G = json.load(open(gem, encoding='utf-8'))
def norm(t):
    t = unicodedata.normalize('NFKC', t).lower()
    t = re.sub(r'^([a-h]|[ivx]+|\d+(\.\d+)*)\.\s', '', t)
    return re.sub(r'[^a-zàâçéèêëîïôûùüœ0-9]+', '', t)
def colonnes(p):
    xs = [r['x0'] for r in p.rects if r['width'] < 2.5 and r['height'] > 8 and r['x0'] > 380] + [l['x0'] for l in p.lines if abs(l['x0'] - l['x1']) < 1 and l['x0'] > 380]
    g = []
    for x in sorted(xs):
        if g and x - g[-1][-1] < 2.5: g[-1].append(x)
        else: g.append([x])
    lefts = [sum(v) / len(v) for v in g]
    lefts = lefts[-5:] if lefts[-1] < 520 else lefts[-6:-1]
    w = (lefts[-1] - lefts[0]) / 4
    return [(x, x + w) for x in lefts]
cache = {}
def page_info(n):
    if n not in cache:
        p = pdf.pages[n - 1]; cols = colonnes(p)
        x_col = cols[0][0] - 1
        horiz = sorted({round(r['top'], 1) for r in p.rects if r['height'] < 2.5 and r['width'] > 60 and r['x0'] < x_col}
                       | {round(l['top'], 1) for l in p.lines if abs(l['top'] - l['bottom']) < 1 and l['x0'] < x_col and l['x1'] - l['x0'] > 60})
        lignes = [l for l in p.extract_text_lines() if l['x1'] < x_col + 5]
        cache[n] = (p, cols, horiz, lignes, M.Rendu(p))
    return cache[n]
SYM = {'apprentissage': '>', 'maitrise': '*', 'reinvestissement': 'B', None: '-'}
res = []
for g in G:
    p, cols, horiz, lignes, R = page_info(g['page'])
    cible = norm(g['texte'])[:28]
    cand = [l for l in lignes if norm(l['text'])[:len(cible)] == cible[:len(norm(l['text'])[:28])] and len(norm(l['text'])) >= 6 and cible.startswith(norm(l['text'])[:min(20, len(cible))])]
    if not cand:
        res.append((g, None, 'ligne introuvable')); continue
    l = cand[0]
    t = max([h for h in horiz if h <= l['top'] + 0.5], default=l['top'] - 3)
    b = min([h for h in horiz if h >= l['bottom'] - 0.5], default=l['bottom'] + 3)
    lu = {a: R.cellule(x0, x1, t, b) for a, (x0, x1) in zip('12345', cols)}
    modes = {}
    for a, (x0, x1) in zip('12345', cols):
        lettres = ''.join(c['text'] for c in sorted(p.chars, key=lambda c: c['x0']) if x0 < (c['x0'] + c['x1']) / 2 < x1 and t < (c['top'] + c['bottom']) / 2 < b and c['text'] in 'LEOÉ')
        if lettres: modes[a] = ''.join(sorted(set(lettres.replace('É', 'E')), key='LEO'.index))
    res.append((g, (lu, modes, round(t), round(b)), ''))
acc = dif = intro = 0
sortie = []
for g, r, err in res:
    gp = {k: g['progression'][k] for k in '12345'}
    gm = {k: v.replace('É', 'E') for k, v in g.get('modes', {}).items()}
    if r is None:
        print('INTROUVABLE', g['id'], g['texte'][:60]); intro += 1; sortie.append({**g, 'verdict': 'introuvable'}); continue
    lu, modes, t, b = r
    ok_p = lu == gp
    ok_m = modes == gm
    v = 'accepte' if ok_p and ok_m else ('accepte_progression' if ok_p else 'desaccord')
    if ok_p: acc += 1
    else:
        dif += 1
        print('DESACCORD', g['id'], g['page'], g['texte'][:50], '| gemini', ''.join(SYM[gp[k]] for k in '12345'), gm, '| pdf', ''.join(SYM[lu[k]] for k in '12345'), modes, f'[{t}-{b}]')
    sortie.append({**g, 'verdict': v, 'lecture_pdf': {'progression': lu, 'modes': modes}})
print('acceptes', acc, 'desaccords', dif, 'introuvables', intro, 'modes differents parmi acceptes', sum(1 for s in sortie if s['verdict'] == 'accepte_progression'))
json.dump(sortie, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
