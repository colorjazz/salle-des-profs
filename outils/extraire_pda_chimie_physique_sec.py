"""Extraction des PDA de chimie et de physique (programmes optionnels de 5e secondaire).

Colonnes : ATS 3e, ATS-SE 4e, ST 3e, ST-STE 4e, puis CHI ou PHY 5e.
Seuls les concepts propres au programme de 5e sont numérotés ; les énoncés sans numéro
(sur fond bleu pâle dans le document) rappellent ce qui a été vu en 3e ou en 4e : champ `rappel`.
Même lecture par pixels que la mathématique : voir extraire_pda_math_sec.py.
Usage : python3 -I extraire_pda_chimie_physique_sec.py source.pdf CHI|PHY sortie.json
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extraire_pda_math_sec as M

NOMS = {'CHI': 'Chimie', 'PHY': 'Physique'}

if __name__ == '__main__':
    src, code, sortie = sys.argv[1:4]
    M.ANNEES[:] = ['ATS-3', 'ATS-SE-4', 'ST-3', 'ST-STE-4', f'{code}-5']
    M.COLONNES_SEQUENCES = ()
    M.LOSANGE = True           # active aussi la lecture des tirets
    M.DERNIERE_JUSQUAU_BORD = True
    M.PAS = (16.5, 26)
    M.SEPARER_FIN = True
    M.RUBRIQUES = True
    M.A_DROITE = True
    M.ANCRES = (code,)
    savoirs, sans_colonnes = M.extraire(src)
    for s in savoirs:
        s.pop('losange', None)
        if s['champ'] != 'Stratégies':
            s['progression'].pop('1er-cycle', None)
        s['texte'] = re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', s['texte'])
        s['chemin'] = [re.sub(r'(?<=[a-zéèà\)]{2})\^\d\b', '', c) for c in s['chemin']]
        if s['note'].startswith('Ligne sans marqueur'):
            s['rappel'] = True
            s['a_verifier'], s['note'] = False, ''
        if s['note'].startswith('Formule'):
            s['a_verifier'], s['note'] = False, 'Exposants notés ^, indices notés _.'
    compteur = collections.Counter()
    for s in savoirs:
        cle = re.sub(r'[^A-Z]', '', (s['champ'] or 'XXX').upper().replace('É', 'E').replace('È', 'E'))[:3]
        compteur[cle] += 1
        s['id'] = f'{code}-{cle}-{compteur[cle]:03d}'
    out = {'discipline': NOMS[code], 'code_discipline': code, 'ordre': 'secondaire',
           'source': src.split('/')[-1], 'annees': M.ANNEES,
           'legende': {'ATS-3': 'Applications technologiques et scientifiques, 3e', 'ATS-SE-4': 'ATS et Science et environnement, 4e',
                       'ST-3': 'Science et technologie, 3e', 'ST-STE-4': 'ST et Science et technologie de l’environnement, 4e',
                       f'{code}-5': f'{NOMS[code]}, 5e (programme optionnel)',
                       '1er-cycle': 'Stratégies seulement : colonne du 1er cycle',
                       'rappel': 'Énoncé non numéroté : connaissance déjà abordée en 3e ou en 4e'},
           'pages_sans_colonnes_reperees': sans_colonnes,
           'bilan': {'nombre_savoirs': len(savoirs), 'rappels': sum(1 for s in savoirs if s.get('rappel')),
                     'a_verifier': sum(s['a_verifier'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'chemin', 'rubrique', 'texte', 'rappel', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False), 'pages sans colonnes :', sans_colonnes, dict(M.CONTROLE))
