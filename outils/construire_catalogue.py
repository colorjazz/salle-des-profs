"""Construit le catalogue des savoirs pour les maquettes (et, plus tard, pour l'application).

Unifie les fichiers de donnees/ en un format unique, par discipline :
  {code, nom, ordre, niveaux, savoirs: [{id, g (groupe), s (section), t (texte), p: {niveau: statut}}]}
Statut : A (flèche, apprentissage), M (étoile, maîtrise), R (case bleue, réinvestissement),
P (au programme, sans progression : Précisions, HQC, Éducation financière, CCQ), ou un objet par
séquence ou programme (ex. {"CST": "M", "TS": "A"} ; {"ST": "M", "STE": "R"}).
Usage : python3 -I outils/construire_catalogue.py donnees/ maquettes/catalogue/
"""
import json, os, re, sys, glob

ST = {'apprentissage': 'A', 'maitrise': 'M', 'reinvestissement': 'R', None: None}
ORDRE_PRIMAIRE = ['FRA', 'MAT', 'SCT', 'US', 'ALS', 'CCQ', 'EPS', 'ADR', 'APL', 'DAN', 'MUS']
NOMS_COURTS = {'Français, langue d\'enseignement': 'Français', "Français, langue d’enseignement": 'Français'}


def court(nom):
    return NOMS_COURTS.get(nom, nom)


def chemin(s, n=2):
    c = [x for x in (s.get('chemin') or []) if x]
    return ' › '.join(re.sub(r'\s+', ' ', x)[:90] for x in c[-n:])


def groupe(s):
    return s.get('champ') or s.get('competence') or s.get('section') or ''


def standard(d, code, niveaux_map=None):
    out = []
    for s in d['savoirs']:
        p = {}
        for k, v in (s.get('progression') or {}).items():
            if isinstance(v, dict):
                v = {q: ST[x] for q, x in v.items() if ST[x]}
                if not v: continue
            else:
                v = ST.get(v)
                if not v: continue
            for niv in (niveaux_map(k) if niveaux_map else [k]):
                if niv: p[niv] = v
        if p:
            out.append({'id': s['id'], 'g': groupe(s), 's': chemin(s), 't': s['texte'], 'p': p})
    return out


def fusion_programmes(d, base, option):
    """ST/STE ou ATS/SE : 1re à 3e simples ; en 4e, un objet {base, option}."""
    out = []
    for s in d['savoirs']:
        pr = s['progression']; p = {}
        for k in ('1', '2', '3'):
            if ST.get(pr.get(k)): p[k] = ST[pr[k]]
        q = {base: ST.get(pr.get('4')), option: ST.get(pr.get('4-' + option))}
        q = {k: v for k, v in q.items() if v}
        if q: p['4'] = q
        if p:
            out.append({'id': s['id'], 'g': groupe(s), 's': chemin(s), 't': s['texte'], 'p': p})
    return out


def sans_progression(savoirs, niveaux, g_cle, n=1):
    return [{'id': s['id'], 'g': s.get(g_cle) or '', 's': chemin(s, n), 't': s['texte'], 'p': {niv: 'P' for niv in niveaux}} for s in savoirs]


def construire(src):
    cat = []
    def ajouter(code, nom, ordre, niveaux, savoirs, **extra):
        if savoirs:
            cat.append({'code': code, 'nom': nom, 'ordre': ordre, 'niveaux': niveaux, 'savoirs': savoirs, **extra})
    J = lambda f: json.load(open(os.path.join(src, f), encoding='utf-8'))
    # PDA standards (primaire 1-6, secondaire 1-5)
    for f in sorted(glob.glob(os.path.join(src, 'pda-*.json'))):
        b = os.path.basename(f)
        if b in ('pda-st-ste-secondaire.json', 'pda-ats-se-secondaire.json', 'pda-ccq-primaire.json', 'pda-ccq-secondaire.json',
                 'pda-chi-secondaire.json', 'pda-phy-secondaire.json', 'pda-als-primaire.json', 'pda-geo-secondaire.json', 'pda-mat-secondaire.json'):
            continue
        d = J(b); ordre = d['ordre']; code = d.get('code_discipline') or b.split('-')[1].upper()
        ajouter(code, court(d['discipline']), ordre, d['annees'], standard(d, code))
    d = J('pda-mat-secondaire.json')
    ajouter('MAT', 'Mathématique', 'secondaire', ['1', '2', '3', '4', '5'], standard(d, 'MAT', lambda k: [] if k == 'primaire' else [k]),
            variantes={'4': ['CST', 'TS', 'SN'], '5': ['CST', 'TS', 'SN']})
    d = J('pda-als-primaire.json')
    ajouter('ALS', 'Anglais, langue seconde', 'primaire', ['1', '2', '3', '4', '5', '6'], standard(d, 'ALS', lambda k: ['1', '2'] if k == '1-2' else [k]))
    d = J('pda-geo-secondaire.json')
    ajouter('GEO', 'Géographie', 'secondaire', ['1', '2'], standard(d, 'GEO', lambda k: ['1', '2']), note='Une seule colonne « 1re ou 2e » dans le document')
    ajouter('ST', 'Science et technologie (ST, STE)', 'secondaire', ['1', '2', '3', '4'], fusion_programmes(J('pda-st-ste-secondaire.json'), 'ST', 'STE'), variantes={'4': ['ST', 'STE']})
    ajouter('ATS', 'Applications technologiques et scientifiques (ATS, SE)', 'secondaire', ['3', '4'],
            [s for s in fusion_programmes(J('pda-ats-se-secondaire.json'), 'ATS', 'SE') if set(s['p']) & {'3', '4'}], variantes={'4': ['ATS', 'SE']})
    for f, code, nom in (('pda-chi-secondaire.json', 'CHI', 'Chimie'), ('pda-phy-secondaire.json', 'PHY', 'Physique')):
        d = J(f)
        sv = [{'id': s['id'], 'g': groupe(s), 's': (s.get('rubrique') + ' · rappel') if s.get('rappel') else chemin(s), 't': s['texte'],
               'p': {'5': ST[s['progression'][code + '-5']]}} for s in d['savoirs'] if ST.get(s['progression'].get(code + '-5'))]
        ajouter(code, nom, 'secondaire', ['5'], sv)
    # sans progression
    for f, code, nom in (('precision-gcu-secondaire.json', 'GCU', 'Géographie culturelle'), ('precision-h20-secondaire.json', 'H20', 'Histoire du 20e siècle'),
                         ('precision-mc4-secondaire.json', 'MC', 'Monde contemporain')):
        ajouter(code, nom, 'secondaire', ['5'], sans_progression(J(f)['savoirs'], ['5'], 'theme', 2))
    ajouter('EDF', 'Éducation financière', 'secondaire', ['5'], sans_progression(J('programme-edf-secondaire.json')['savoirs'], ['5'], 'enjeu'))
    h = J('programme-hqc-secondaire.json'); sv = []
    for per in h['periodes']:
        niv = per['niveau'].replace('S', '')
        for th in per['themes']:
            for el in th['elements']:
                sv.append({'id': el['id'], 'g': f"{per['bornes']} · {per['titre']}", 's': th['theme'], 't': el['texte'], 'p': {niv: 'P'}})
    ajouter('HQC', 'Histoire du Québec et du Canada', 'secondaire', ['3', '4'], sv)
    for ordre in ('primaire', 'secondaire'):
        c = J(f'pda-ccq-{ordre}.json'); sv = []
        for bloc in c['contenus']:
            for col in bloc['colonnes']:
                tete = col.get('sous_theme') or col.get('concept_principal') or ''
                for e in col['elements']:
                    t = e.get('element') or tete
                    if e.get('notions'): t += ' — ' + e['notions']
                    sv.append({'id': e['id'], 'g': bloc.get('theme') or tete, 's': tete, 't': t, 'p': {bloc['annee']: 'P'}})
        cyc = {'primaire': {'1': ['1', '2'], '2': ['3', '4'], '3': ['5', '6']}, 'secondaire': {'1': ['1', '2'], '2': ['3', '4', '5']}}[ordre]
        for ind in c['indicateurs']:
            p = {n: 'P' for k, v in ind['cycles'].items() if v for n in cyc[k]}
            if p:
                t = ind['enonce'] + (' ' + ind['precision'] if ind.get('precision') else '')
                sv.append({'id': ind['id'], 'g': 'Indicateurs de progression' + (' · ' + ind['competence'] if ind.get('competence') else ''), 's': ind['composante'], 't': t, 'p': p})
        ajouter('CCQ', 'Culture et citoyenneté québécoise', ordre, sorted({n for s in sv for n in s['p']}), sv)
    return cat


if __name__ == '__main__':
    src, dst = sys.argv[1:3]
    os.makedirs(dst, exist_ok=True)
    cat = construire(src)
    index = []
    for d in cat:
        fichier = f"{d['ordre'][:3]}-{d['code'].lower()}.json"
        json.dump(d, open(os.path.join(dst, fichier), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        index.append({'code': d['code'], 'nom': d['nom'], 'ordre': d['ordre'], 'niveaux': d['niveaux'], 'fichier': fichier,
                      'n': len(d['savoirs']), **({'variantes': d['variantes']} if d.get('variantes') else {})})
    rang = lambda e: (e['ordre'], ORDRE_PRIMAIRE.index(e['code']) if e['code'] in ORDRE_PRIMAIRE else 50, e['nom'])
    index.sort(key=rang)
    json.dump({'disciplines': index}, open(os.path.join(dst, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    taille = sum(os.path.getsize(os.path.join(dst, e['fichier'])) for e in index)
    print(len(index), 'disciplines,', sum(e['n'] for e in index), 'savoirs,', round(taille / 1e6, 2), 'Mo')
    for e in index:
        print(f"  {e['ordre'][:4]} {e['code']:<4} {e['nom'][:45]:<45} niveaux {','.join(e['niveaux']):<12} {e['n']}")
