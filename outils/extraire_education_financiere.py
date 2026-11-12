"""Extraction du programme Éducation financière (5e secondaire, 2018) et de son cadre d'évaluation (2016).

Une compétence (Prendre position sur un enjeu financier), quatre composantes, trois enjeux financiers
avec leurs concepts, et la Précision des apprentissages : 1. section > a. énoncé. Les composantes sont
dessinées dans une image (page 8 du programme) : elles sont recopiées ici d'après la page.
Usage : python3 -I extraire_education_financiere.py programme.pdf cadre.pdf sortie.json
"""
import json, re, subprocess, sys, collections

COMPOSANTES = {   # page 8 du programme (image), recopiées d'après la page
    'Cerner la situation': ['Préciser les besoins', 'Examiner le budget', 'Établir des contraintes', 'Considérer des éléments du contexte socioéconomique'],
    'Examiner des options': ['Considérer les coûts afférents', 'Déterminer les risques', 'Déterminer des avantages et des inconvénients', 'Choisir une option'],
    'Considérer les aspects légaux': ['Reconnaître des droits', 'Reconnaître des responsabilités', 'Connaître des instances légales où faire valoir ses droits'],
    'Relativiser sa position': ['Comparer ses choix à ceux d’autres', 'Reconnaître des influences sur son choix', 'Reconsidérer son choix'],
}


def texte_pages(pdf):
    n = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
    return [subprocess.run(['pdftotext', '-layout', '-f', str(p), '-l', str(p), pdf, '-'], capture_output=True, text=True).stdout for p in range(1, n + 1)]


def nettoyer(t):
    t = re.sub(r'\s+', ' ', t).strip()
    return re.sub(r'(?<=\w)- (?=\w)', '-', t)


def extraire(programme):
    pages = texte_pages(programme)
    enjeux, enjeu, concepts = [], None, {}
    for num, page in enumerate(pages, 1):
        lignes = page.split('\n')
        for l in lignes:
            m = re.match(r'^Enjeu financier\s{2,}(.+?)\s*$', l)
            if m:
                nom = nettoyer(m.group(1))
                enjeu = next((e for e in enjeux if e['enjeu'] == nom), None)
                if enjeu is None:
                    enjeu = {'enjeu': nom, 'concepts': [], 'sections': []}; enjeux.append(enjeu)
            m = re.match(r'^Concepts\s*:\s*(.+?)\s*$', l)
            if m and enjeu:
                enjeu['concepts'] = [c.strip() for c in m.group(1).split(',')]
        if 'Précision des apprentissages' not in page and not (enjeu and enjeu['sections'] and re.search(r'^\s{0,3}\d+\.\s', page, re.M)):
            continue
        courant = None
        for l in lignes:
            if not l.strip() or l.startswith(('Programme de formation', 'Précision des apprentissages', 'Enjeu financier', 'Concepts')) or re.fullmatch(r'\s*\d{1,2}\s*', l):
                courant = None if not l.strip() else courant
                continue
            ms = re.match(r'^\s{0,3}(\d+)\.\s+(.*)$', l)
            mi = re.match(r'^\s{4,9}([a-z])\.\s+(.*)$', l)
            if ms and enjeu:
                enjeu['sections'].append({'section': f"{ms.group(1)}. {nettoyer(ms.group(2))}", 'enonces': []}); courant = None
            elif mi and enjeu and enjeu['sections']:
                courant = {'lettre': mi.group(1), 'texte': mi.group(2)}
                enjeu['sections'][-1]['enonces'].append(courant)
            elif courant is not None and re.match(r'^\s{8,}\S', l):
                courant['texte'] += ' ' + l.strip()
    for e in enjeux:   # la bibliographie, en fin de document, ressemble à des sections numérotées
        e['sections'] = [s for s in e['sections'] if s['enonces']]
    return enjeux


def cadre(pdf):
    t = '\n'.join(texte_pages(pdf))
    criteres = []
    if 'Maîtrise des connaissances' in t: criteres.append('Maîtrise des connaissances')
    if 'Justification appropriée du choix' in t: criteres.append('Justification appropriée du choix')
    m = re.search(r'Justification appropriée du choix\s+Explication qui présente des avantages de l’option\s+choisie et des inconvénients des autres options\s+associées à la situation\.', t)
    return {'competence': 'Prendre position sur un enjeu financier', 'ponderation': '100 %', 'criteres': criteres,
            'precision_critere': {'Justification appropriée du choix': 'Explication qui présente des avantages de l’option choisie et des inconvénients des autres options associées à la situation.'} if m else {},
            'note': 'Les connaissances sont évaluées aux moments choisis par l’enseignant, qui détermine l’importance à accorder, dans le résultat de l’élève, aux différentes dimensions à évaluer.'}


if __name__ == '__main__':
    prog, cad, sortie = sys.argv[1:4]
    enjeux = extraire(prog)
    savoirs = []
    cles = {'Consommer des biens et des services': 'CON', 'Intégrer le monde du travail': 'TRA', 'Poursuivre des études': 'ETU'}
    for e in enjeux:
        k = 0
        for s in e['sections']:
            for x in s['enonces']:
                k += 1
                x['texte'] = nettoyer(x['texte'])
                savoirs.append({'id': f"EDF-{cles.get(e['enjeu'], 'XXX')}-{k:03d}", 'enjeu': e['enjeu'], 'chemin': [s['section']],
                                'texte': f"{x['lettre']}. {x['texte']}"})
    out = {'discipline': 'Éducation financière', 'code_discipline': 'EDF', 'ordre': 'secondaire', 'annee': '5',
           'source': prog.split('/')[-1], 'source_cadre': cad.split('/')[-1], 'version': 'programme 2018, cadre d’évaluation avril 2016',
           'duree': '50 heures',
           'type': 'Précision des apprentissages : liste d’énoncés, sans progression par année (un seul niveau, 5e secondaire)',
           'competence': {'nom': 'Prendre position sur un enjeu financier', 'composantes': COMPOSANTES},
           'enjeux': [{'enjeu': e['enjeu'], 'concepts': e['concepts'], 'sections': [s['section'] for s in e['sections']]} for e in enjeux],
           'cadre_evaluation': cadre(cad),
           'bilan': {'nombre_savoirs': len(savoirs), 'par_enjeu': dict(collections.Counter(s['enjeu'] for s in savoirs))},
           'savoirs': savoirs}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False))
    for e in out['enjeux']: print(e)
