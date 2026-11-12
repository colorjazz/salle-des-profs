"""Valide une réponse de Gemini (gemini/11) avant de l'utiliser : modules, affectation, libellés.

Contrôles : chaque savoir du catalogue est affecté à un seul module existant ; aucun code inventé ;
8 à 20 modules ; titres courts ; un libellé par savoir, sans code et de longueur raisonnable.
Si tout est bon, la réponse est copiée dans gemini/resultats/modules/, puis il suffit de relancer
outils/construire_modules.py.
Usage : python3 -I outils/valider_modules.py reponse.json
"""
import json, os, re, sys

def main(f):
    r = json.load(open(f, encoding='utf-8'))
    cat = json.load(open(os.path.join('maquettes/catalogue', r['fichier']), encoding='utf-8'))
    ids = {s['id'] for s in cat['savoirs']}
    mods = {m['id'] for m in r['modules']}
    err, avert = [], []
    if not 8 <= len(mods) <= 20: avert.append(f'{len(mods)} modules (attendu : 8 à 20)')
    for m in r['modules']:
        if len(m['titre']) > 60 or re.search(r'[A-Z]{3}-', m['titre']): err.append(f"titre trop long ou avec code : {m['titre']}")
    aff = r['affectation']
    manquants = ids - set(aff); inventes = set(aff) - ids
    if manquants: err.append(f'{len(manquants)} savoirs sans module (ex. {sorted(manquants)[:5]})')
    if inventes: err.append(f'{len(inventes)} codes inconnus (ex. {sorted(inventes)[:5]})')
    hors = {i for i, m in aff.items() if m not in mods}
    if hors: err.append(f'{len(hors)} savoirs affectés à un module inexistant')
    lib = r.get('libelles', {})
    sans = ids - set(lib)
    if sans: avert.append(f'{len(sans)} savoirs sans libellé (le texte officiel sera affiché)')
    for i, l in lib.items():
        if i not in ids: err.append(f'libellé pour un code inconnu : {i}'); continue
        if re.search(r'\b[A-Z]{2,4}-[A-Z]{3}-\d{3}', l) or len(l) > 220: avert.append(f'libellé à revoir ({i}) : {l[:80]}')
    print(json.dumps({'fichier': r['fichier'], 'modules': len(mods), 'savoirs': len(ids), 'libelles': len(lib), 'erreurs': err, 'avertissements': avert[:20]}, ensure_ascii=False, indent=1))
    if not err:
        dst = os.path.join('gemini/resultats/modules', r['fichier'])
        json.dump(r, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('accepté : copié dans', dst, '— relancer outils/construire_modules.py')

if __name__ == '__main__':
    main(sys.argv[1])
