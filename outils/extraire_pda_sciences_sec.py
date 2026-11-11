"""Extraction des PDA de science au secondaire (deux documents, quatre programmes).

- Science et technologie (ST) et Science et technologie de l'environnement (STE) : un seul document ;
- Applications technologiques et scientifiques (ATS) et Science et environnement (SE) : un seul document.
Colonnes : 1re et 2e (1er cycle), 3e et 4e du programme obligatoire (ST ou ATS), puis 4e du programme
optionnel (STE ou SE). Le losange marque les énoncés propres au programme obligatoire.
Même lecture que la mathématique (cellules lues par pixels) : voir extraire_pda_math_sec.py.
Usage : python3 -I extraire_pda_sciences_sec.py source.pdf OBLIGATOIRE OPTIONNEL sortie.json
        (ex. ST STE, ou ATS SE)
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M

NOMS = {'ST': 'Science et technologie', 'STE': 'Science et technologie de l’environnement',
        'ATS': 'Applications technologiques et scientifiques', 'SE': 'Science et environnement'}

if __name__ == '__main__':
    src, oblig, option, sortie = sys.argv[1:5]
    M.ANNEES[:] = ['1', '2', '3', '4', f'4-{option}']
    M.COLONNES_SEQUENCES = ()
    M.LOSANGE = True
    M.DERNIERE_JUSQUAU_BORD = True
    savoirs, sans_colonnes = M.extraire(src)
    for s in savoirs:
        s['texte'] = re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', s['texte'])   # appels de note
        s['chemin'] = [re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', c) for c in s['chemin']]
        if s['champ'] == 'Stratégies' and re.search(r'\sP(\s|$)', s['texte']):
            # colonne « P » : stratégie déjà abordée au primaire
            s['texte'] = re.sub(r'\s+', ' ', re.sub(r'\sP(?=\s|$)', '', s['texte'])).strip()
            s['abordee_au_primaire'] = True
            if s['note'].startswith('Fraction'):
                s['a_verifier'], s['note'] = False, ''
        if s['note'].startswith('Formule'):   # pas de formules empilées ici : exposants et indices suffisent
            s['a_verifier'], s['note'] = False, 'Exposants notés ^, indices notés _.'
    # fin de phrase coupée par un trait du tableau (« de rotation) ») : rattachée à l'énoncé précédent
    garde = []
    for s in savoirs:
        if garde and s['a_verifier'] and s['note'].startswith('Ligne sans marqueur') and s['texte'][:1].islower() and s['page'] - garde[-1]['page'] in (0, 1):
            garde[-1]['texte'] += ' ' + s['texte']
            continue
        garde.append(s)
    savoirs[:] = garde
    compteur = collections.Counter()
    for s in savoirs:
        cle = re.sub(r'[^A-Z]', '', (s['champ'] or 'XXX').upper().replace('É', 'E').replace('’', ''))
        cle = {'LUNIVERSMATERIEL': 'MAT', 'LUNIVERSVIVANT': 'VIV', 'LATERREETLESPACE': 'TER',
               'LUNIVERSTECHNOLOGIQUE': 'TEC', 'TECHNIQUES': 'TCH', 'STRATEGIES': 'STR'}.get(cle, cle[:3])
        compteur[cle] += 1
        s['id'] = f'{oblig}-{cle}-{compteur[cle]:03d}'
    out = {'discipline': f'{NOMS[oblig]} et {NOMS[option]}', 'programmes': {oblig: NOMS[oblig], option: NOMS[option]},
           'ordre': 'secondaire', 'source': src.split('/')[-1], 'annees': M.ANNEES,
           'legende': {'1, 2': f'{oblig} 1er cycle', '3, 4': f'{oblig} 2e cycle (programme obligatoire)',
                       f'4-{option}': f'{option} 4e secondaire (programme optionnel)',
                       'abordee_au_primaire': 'Stratégies : la lettre P du document (déjà abordée au primaire)',
                       'losange': f'Énoncé propre au programme obligatoire {oblig} ; la plupart se retrouvent aussi en {option}'},
           'pages_sans_colonnes_reperees': sans_colonnes,
           'bilan': {'nombre_savoirs': len(savoirs), 'losanges': sum(1 for s in savoirs if s.get('losange')),
                     'a_verifier': sum(s['a_verifier'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'chemin', 'texte', 'losange', 'abordee_au_primaire', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False), 'pages sans colonnes :', sans_colonnes, dict(M.CONTROLE))
