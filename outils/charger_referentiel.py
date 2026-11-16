"""Produit le SQL qui charge le référentiel (programmes, savoirs, modules) dans la base Postgres.

Source : maquettes/catalogue/ (catalogue et modules déjà construits).
Usage : python3 -I outils/charger_referentiel.py | psql "$URL_PROPRIO"
Le chargement remplace savoirs et modules dans une transaction ; les programmes sont mis à jour sur place.
Il ne touche à aucune donnée d'enseignante (aucune suppression en cascade).
"""
import hashlib, json, os, sys

CAT = 'maquettes/catalogue'

def q(x):
    if x is None: return 'null'
    if isinstance(x, (dict, list)) and not isinstance(x, str) and isinstance(x, dict): x = json.dumps(x, ensure_ascii=False, separators=(',', ':'))
    return "'" + str(x).replace("'", "''") + "'"

def tableau(xs):
    return "array[" + ','.join(q(x) for x in xs) + "]::text[]" if xs else "'{}'::text[]"

def main(out=sys.stdout):
    index = json.load(open(os.path.join(CAT, 'index.json'), encoding='utf-8'))
    w = out.write
    w("begin;\nset local search_path = sdp, public;\ndelete from savoirs_modules; delete from modules; delete from savoirs;\n")
    total = 0
    for e in index['disciplines']:
        brut = open(os.path.join(CAT, e['fichier']), 'rb').read()
        d = json.loads(brut)
        prog = e['fichier'].removesuffix('.json')
        version = hashlib.sha256(brut).hexdigest()[:12]
        w(f"insert into programmes values ({q(prog)}, {q(e['code'])}, {q(e['nom'])}, {q(e['ordre'])}, {tableau(e['niveaux'])}, {q(version)})\n  on conflict (programme) do update set code = excluded.code, nom = excluded.nom, ordre = excluded.ordre, niveaux = excluded.niveaux, version = excluded.version;\n")
        lignes = [f"({q(prog)},{q(s['id'])},{q(s.get('g',''))},{q(s.get('s',''))},{q(s['t'])},{q(s.get('p',{}))}::jsonb)" for s in d['savoirs']]
        for i in range(0, len(lignes), 500):
            w("insert into savoirs values\n" + ',\n'.join(lignes[i:i+500]) + ";\n")
        total += len(lignes)
        fm = os.path.join(CAT, 'modules', e['fichier'])
        if os.path.exists(fm):
            m = json.load(open(fm, encoding='utf-8'))
            w("insert into modules values\n" + ',\n'.join(f"({q(prog)},{q(x['id'])},{r},{q(x['titre'])},{q(x.get('description',''))})" for r, x in enumerate(m['modules'])) + ";\n")
            lib = m.get('libelles', {})
            ids = {s['id'] for s in d['savoirs']}
            aff = [(s, mod) for s, mod in m['affectation'].items() if s in ids]
            for i in range(0, len(aff), 500):
                w("insert into savoirs_modules values\n" + ',\n'.join(f"({q(prog)},{q(s)},{q(mod)},{q(lib.get(s))})" for s, mod in aff[i:i+500]) + ";\n")
    w("commit;\n")
    print(f'{len(index["disciplines"])} programmes, {total} savoirs', file=sys.stderr)

if __name__ == '__main__':
    main()
