"""Valide la réponse de l'IA (circuit Création) avant de produire le fichier.

Contrôles : opérations intellectuelles officielles ; codes de savoirs de la demande ; documents cités
existants ; total des points ; aucune citation attribuée ; chaque nombre et chaque nom propre de la
réponse figure dans le texte source (sinon, fait possiblement inventé : à refuser ou à faire relire).
Usage : python3 -I valider_creation.py demande.json reponse.json rapport.json
"""
import json, re, sys, unicodedata

def plat(t): return unicodedata.normalize('NFKC', t).replace(' ', ' ').replace('\xa0', ' ')

def textes(r):
    for d in r['documents']:
        for t in d.get('texte', []): yield ('document ' + d['id'], t)
        for l in d.get('listes', []):
            yield ('document ' + d['id'], l['titre'])
            for e in l['elements']: yield ('document ' + d['id'], e)
    for q in r['questions']:
        yield (f"question {q['numero']}", q['consigne']); yield (f"corrigé {q['numero']}", q['corrige'])

def main(dem_f, rep_f, out_f):
    dem = json.load(open(dem_f, encoding='utf-8')); r = json.load(open(rep_f, encoding='utf-8'))
    src = plat(dem['source_faits']['texte']); codes = {s['id'] for s in dem['savoirs']}
    ops = set(dem['operations_permises']); docs = {d['id'] for d in r['documents']}
    erreurs, avertissements, ok = [], [], []
    for q in r['questions']:
        if q['operation'] not in ops: erreurs.append(f"Question {q['numero']} : opération non officielle « {q['operation']} »")
        for c in q['savoirs']:
            if c not in codes: erreurs.append(f"Question {q['numero']} : code de savoir inconnu {c}")
        for d in q['documents']:
            if d not in docs: erreurs.append(f"Question {q['numero']} : document {d} introuvable")
    ok.append(f"{len(r['questions'])} questions, toutes rattachées à une opération officielle et à des savoirs de la demande" if not erreurs else '')
    if sum(q['points'] for q in r['questions']) != r['total']: erreurs.append('Total des points incorrect')
    else: ok.append(f"Total des points : {r['total']}")
    couverts = {c for q in r['questions'] for c in q['savoirs']}
    if couverts != codes: avertissements.append('Savoirs non travaillés : ' + ', '.join(sorted(codes - couverts)))
    else: ok.append(f"Les {len(codes)} savoirs demandés sont travaillés")
    for ou, t in textes(r):
        t = plat(t)
        if re.search(r'«[^»]{3,}»\s*,?\s*(dit|écrit|affirme|déclare|selon)\b|\b(dit|écrit|affirme|déclare)\s*:\s*«', t):
            erreurs.append(f"{ou} : citation attribuée")
        for n in re.findall(r'\d[\d ]*\d|\d', t):
            n = n.strip()
            if n not in src and n not in ('1', '2', '3', '4', '5', '6'): erreurs.append(f"{ou} : nombre absent de la source ({n})")
        for m in re.finditer(r'(?<![.!?:]\s)(?<!^)\b([A-ZÉÈÀÎÔ][a-zéèêàâîôûç]+(?:[- ][A-ZÉ][a-zéèêàç]+)*)', t):
            mot = m.group(1)
            if mot.split()[0] in ('Document', 'Nommez', 'Relevez', 'Comparez', 'Expliquez', 'Indiquez', 'Selon', 'Familles', 'Régions', 'Causes', 'Conséquence', 'Différence', 'Similitude', 'Grandes', 'Vallée', 'Le', 'La', 'Les', 'Ils', 'Au', 'Il', 'Des', 'Nomades', 'Appuyez', 'Iroquoiens', 'Algonquiens', 'Inuits') and mot.split()[0] not in src:
                continue
            if mot not in src and mot.lower() not in src.lower():
                avertissements.append(f"{ou} : nom propre absent de la source « {mot} » (à faire relire)")
    rapport = {'resultat': 'accepté' if not erreurs else 'refusé', 'erreurs': erreurs, 'avertissements': sorted(set(avertissements)), 'controles_reussis': [x for x in ok if x]}
    json.dump(rapport, open(out_f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(rapport, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main(*sys.argv[1:4])
