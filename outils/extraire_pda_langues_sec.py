"""Extraction des PDA de langues au secondaire : anglais langue seconde (base, enrichi), espagnol.

Grille : une colonne par année (1re à 5e en anglais ; 3e à 5e en espagnol). En anglais, la lettre P
(colonne Primaire) indique que certaines notions ont déjà été vues au primaire : champ `vu_au_primaire`.
Lecture par pixels comme en mathématique : voir extraire_pda_math_sec.py.
Usage : python3 -I extraire_pda_langues_sec.py source.pdf CODE "Discipline" 1,2,3,4,5 sortie.json
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M

if __name__ == '__main__':
    src, code, disc, annees, sortie = sys.argv[1:6]
    M.ANNEES[:] = annees.split(',')
    M.COLONNES_SEQUENCES = ()
    M.LOSANGE = True            # lecture des tirets des sous-énoncés
    M.SEPARER_FIN = True
    savoirs, sans_colonnes = M.extraire(src)
    # lignes de la légende captées sous l'en-tête (« P : La lettre… », « L’élève apprend… »)
    savoirs[:] = [s for s in savoirs if not re.match(r'^(P\s*:\s*La lettre|L’élève (apprend|le fait|réutilise))', s['texte'])]
    for s in savoirs:
        s.pop('losange', None)
        if re.search(r'\sP(\s|$)', s['texte']):
            s['texte'] = re.sub(r'\s+', ' ', re.sub(r'\sP(?=\s|$)', '', s['texte'])).strip()
            s['vu_au_primaire'] = True
            if s['note'].startswith('Fraction'):
                s['a_verifier'], s['note'] = False, ''
        s['texte'] = re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', s['texte'])
        s['texte'] = re.sub(r'\^(e|er|re|es|ers|res)\b', r'\1', s['texte'])
        s['texte'] = re.sub(r'(?<=\w)- (?=\w)', '-', s['texte'])
        s['chemin'] = [re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', c) for c in s['chemin']]
        if s['note'].startswith('Formule') and '=' not in s['texte']:
            s['a_verifier'], s['note'] = False, ''
    # fin de phrase coupée par un trait (rattachée à l'énoncé précédent)
    garde = []
    for s in savoirs:
        if garde and s['a_verifier'] and s['note'].startswith('Ligne sans marqueur') and s['texte'][:1].islower() and s['page'] - garde[-1]['page'] in (0, 1):
            garde[-1]['texte'] += ' ' + s['texte']; continue
        garde.append(s)
    savoirs[:] = garde
    vides = {'le', 'la', 'les', 'de', 'des', 'du', 'et', 'l', 'd'}
    compteur = collections.Counter()
    for s in savoirs:
        mots = [m for m in re.split(r"[\s’'-]+", s['champ'] or 'XXX') if m.lower() not in vides]
        cle = re.sub(r'[^A-Z]', '', mots[0].upper().replace('É', 'E').replace('È', 'E'))[:3] if mots else 'XXX'
        compteur[cle] += 1
        s['id'] = f'{code}-{cle}-{compteur[cle]:03d}'
    out = {'discipline': disc, 'code_discipline': code, 'ordre': 'secondaire', 'source': src.split('/')[-1], 'annees': M.ANNEES,
           'pages_sans_colonnes_reperees': sans_colonnes,
           'bilan': {'nombre_savoirs': len(savoirs), 'vus_au_primaire': sum(1 for s in savoirs if s.get('vu_au_primaire')),
                     'a_verifier': sum(s['a_verifier'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'section', 'chemin', 'texte', 'vu_au_primaire', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False), 'pages sans colonnes :', sans_colonnes, dict(M.CONTROLE))
