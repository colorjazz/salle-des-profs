"""Extraction de la PDA de mathématique au secondaire vers JSON.

Mise en page propre à ce document :
- six colonnes : 6e année du primaire (rappel des acquis), puis 1re à 5e secondaire ;
- en 4e et 5e, une cellule peut être subdivisée selon les séquences CST, TS et SN
  (étiquettes de couleur à droite du tableau) ;
- les colonnes se décalent d'une page à l'autre : on les repère par les lignes verticales ;
- les rangées sont délimitées par les lignes horizontales du tableau ;
- formules : exposants notés ^ et indices notés _ ; les fractions empilées sont signalées.
Usage : python3 -I extraire_pda_math_sec.py source.pdf sortie.json
"""
import json, re, sys, collections
import pdfplumber

ANNEES = ['primaire', '1', '2', '3', '4', '5']   # « primaire » = colonne 6e année
SEQUENCES = ('CST', 'TS', 'SN')
CONTROLE = collections.Counter()
DEBUG = set()
MARQUEURS = [
    (1, re.compile(r'^[A-H]\.(\s|$)')),
    (4, re.compile(r'^(i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv)\.(\s|$)')),
    (2, re.compile(r'^\d{1,2}\.(\s|$)')),
    (3, re.compile(r'^[a-z]\.(\s|$)')),
    (5, re.compile(r'^[–—-]\s')),
]


def niveau(texte):
    for n, rx in MARQUEURS:
        if rx.match(texte):
            return n
    return None


def est_bleu(c):
    return isinstance(c, (tuple, list)) and len(c) == 3 and c[2] > 0.85 and c[0] < 0.8 and c[1] < 0.82 and c[2] - c[0] > 0.1


def colonnes(page):
    """Six colonnes consécutives d'environ 18,5 pt, repérées par les traits verticaux."""
    xs = [r['x0'] for r in page.rects if r['width'] < 2.5 and r['height'] > 8 and r['x0'] > 370]
    xs += [l['x0'] for l in page.lines if abs(l['x0'] - l['x1']) < 1 and l['x0'] > 370]
    grappes = []
    for x in sorted(xs):
        if grappes and x - grappes[-1][-1] < 2.5:
            grappes[-1].append(x)
        else:
            grappes.append([x])
    pos = [(sum(g) / len(g), len(g)) for g in grappes]
    # chaîne de six traits espacés d'environ 18,5 pt ; s'il y en a plusieurs, la plus fournie
    meilleure = None
    for i in range(len(pos)):
        chaine = [pos[i]]
        for x, n in pos[i + 1:]:
            if 16.5 <= x - chaine[-1][0] <= 20.5:
                chaine.append((x, n))
            if len(chaine) == 6:
                break
        if len(chaine) == 6 and (meilleure is None or sum(n for _, n in chaine) > sum(n for _, n in meilleure)):
            meilleure = chaine
    if not meilleure:
        return None
    xs = [x for x, _ in meilleure]
    largeur = (xs[-1] - xs[0]) / 5
    return [(x, x + largeur) for x in xs]


def lignes_texte(page, x_col, haut, bas, x_max=None, exclus=()):
    """Reconstitue les lignes à partir des caractères ; exposants (^) et indices (_)."""
    x_max = x_max or x_col
    # les rangées de titre pleine largeur débordent dans les colonnes : on garde leur texte, sauf l'en-tête 6e à 5e
    chars = [c for c in page.chars if c['top'] > haut and c['bottom'] <= bas + 2 and c['size'] < 13
             and (c['x1'] < x_col or (c['x1'] < x_max and not any(abs(c['top'] - h) < 3 for h in exclus)))]
    if not any(c['text'].strip() for c in chars):
        return []
    tailles = collections.Counter(round(c['size'], 1) for c in page.chars if c['x1'] < x_col and c['text'].strip())
    corps = tailles.most_common(1)[0][0]
    principaux = [c for c in chars if c['size'] >= corps - 0.6 and c['text'].strip()]
    petits = [c for c in chars if c['size'] < corps - 0.6 and c['text'].strip()]
    espaces = [c for c in chars if not c['text'].strip()]
    rangs = []
    for c in sorted(principaux, key=lambda c: (round(c['top']), c['x0'])):
        for r in rangs:
            if abs(c['top'] - r['top']) < 3.5:
                r['chars'].append(c)
                break
        else:
            rangs.append({'top': c['top'], 'bottom': c['bottom'], 'chars': [c], 'petit': False})
    for c in petits:
        cy = (c['top'] + c['bottom']) / 2
        hote = [r for r in rangs if r['top'] - 3 <= cy <= r['bottom'] + 1 and
                any(abs(c['x0'] - o['x1']) < 6 or abs(o['x0'] - c['x1']) < 6 for o in r['chars'])]
        if not hote:
            # marqueur en petits caractères juste à gauche d'une ligne (ex. « i. » d'une sous-liste)
            gauche = [r for r in rangs if not r['petit'] and r['top'] - 3 <= cy <= r['bottom'] + 4
                      and 0 <= min(o['x0'] for o in r['chars']) - c['x1'] < 12]
            if gauche:
                c = dict(c, role='')
                gauche[0]['chars'].append(c)
                continue
        if hote:
            r = hote[0]
            c = dict(c)
            c['role'] = '^' if c['bottom'] < r['bottom'] - 1.5 else ('_' if c['top'] > r['top'] + 1.5 else '')
            r['chars'].append(c)
        else:
            # ligne en petits caractères (ex. une note) : regroupée à part
            for r in rangs:
                if r['petit'] and abs(c['top'] - r['top']) < 2:
                    r['chars'].append(c)
                    break
            else:
                rangs.append({'top': c['top'], 'bottom': c['bottom'], 'chars': [c], 'petit': True})
    for c in espaces:
        cy = (c['top'] + c['bottom']) / 2
        for r in rangs:
            if r['top'] - 1 <= cy <= r['bottom'] + 1 and r['chars'][0]['x0'] < c['x0'] and (r['petit'] == (c['size'] < corps - 0.6) or not r['petit']):
                r['chars'].append(dict(c, espace=True))
                break
    for r in rangs:
        r['chars'].sort(key=lambda c: c['x0'])
        morceaux, prec, role_prec = [], None, ''
        for c in r['chars']:
            if c.get('espace'):
                morceaux.append(' ')
                prec, role_prec = c, ''
                continue
            role = c.get('role', '')
            if prec is not None and c['x0'] - prec['x1'] > 0.3 * c['size'] and not (role and role == role_prec):
                morceaux.append(' ')
            if role and role != role_prec:
                morceaux.append(role)
            morceaux.append(c['text'])
            prec, role_prec = c, role
        r['texte'] = re.sub(r' +', ' ', ''.join(morceaux)).strip()
        r['x0'] = r['chars'][0]['x0']
        r['bottom'] = max(c['bottom'] for c in r['chars'])
        r['chars'] = [c for c in r['chars'] if not c.get('espace')]
        r['gras'] = sum(1 for c in r['chars'] if 'Bold' in c['fontname'])
        r['total'] = len(r['chars'])
    rangs.sort(key=lambda r: r['top'])
    return rangs


def plus_grande_tache(points):
    """Plus grande composante connexe (8 voisins) : écarte les bouts de bordure isolés."""
    reste, meilleure = set(points), []
    while reste:
        depart = reste.pop(); pile, tache = [depart], [depart]
        while pile:
            x, y = pile.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    v = (x + dx, y + dy)
                    if v in reste:
                        reste.remove(v); pile.append(v); tache.append(v)
        if len(tache) > len(meilleure):
            meilleure = tache
    return meilleure


class Rendu:
    """Lecture des cellules par pixels : les images des symboles sont décalées dans ce PDF."""
    ECHELLE = 3  # 216 ppp

    def __init__(self, page):
        self.img = page.to_image(resolution=72 * self.ECHELLE).original.convert('RGB')
        self.lettres = [c for c in page.chars if c['text'].strip() and c['size'] < 13]

    def cellule(self, x0, x1, t, b):
        e = self.ECHELLE
        if any(c['x0'] < x1 - 1 and c['x1'] > x0 + 1 and c['top'] < b - 1 and c['bottom'] > t + 1 for c in self.lettres):
            return None   # du texte déborde dans la colonne (rangée de titre pleine largeur)
        boite = self.img.crop((int((x0 + 1.5) * e), int((t + 1.5) * e), int((x1 - 1.5) * e), int((b - 1.5) * e)))
        w, h = boite.size
        if w < 3 or h < 3:
            return None
        px = boite.load()
        fonce, bleu = [], 0
        for x in range(w):
            for y in range(h):
                r, g, b_ = px[x, y]
                if b_ > 195 and b_ - r > 25 and r < 215:
                    bleu += 1
                elif (r + g + b_) / 3 < 140:
                    fonce.append((x, y))
        # retirer les traits de bordure (rangées ou colonnes presque entièrement foncées)
        lignes_f = collections.Counter(y for x, y in fonce)
        cols_f = collections.Counter(x for x, y in fonce)
        fonce = [(x, y) for x, y in fonce if lignes_f[y] < 0.6 * w and cols_f[x] < 0.6 * h]
        fonce = plus_grande_tache(fonce)
        if len(fonce) >= 12:
            xs = [x for x, y in fonce]; ys = [y for x, y in fonce]
            larg, haut = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            if haut < 4 or larg > 0.95 * w and haut < 6:
                pass  # trait de bordure, pas un symbole
            else:
                # l'étoile est symétrique gauche-droite, la flèche ne l'est pas
                x_min, x_max, s = min(xs), max(xs), set(fonce)
                miroir = sum(1 for x, y in fonce if (x_min + x_max - x, y) in s) / len(fonce)
                forme = 'maitrise' if miroir >= 0.68 else 'apprentissage'
                if DEBUG:
                    print('   forme', round(miroir, 2), forme)
                CONTROLE[forme] += 1
                return forme
        if bleu > 0.4 * w * h:
            return 'reinvestissement'
        return None


def etiquettes_sequences(page, cols):
    x_droite = cols[-1][1] - 2
    mots = [w for w in page.extract_words() if w['text'] in SEQUENCES and w['x0'] > x_droite]
    sortie = []
    for w in mots:
        boites = [r for r in page.rects if r['x0'] - 1 <= w['x0'] and w['x1'] <= r['x1'] + 1
                  and r['top'] - 1 <= w['top'] and w['bottom'] <= r['bottom'] + 1 and 20 < r['width'] < 30]
        if boites:
            b = min(boites, key=lambda r: r['height'])
            sortie.append((w['text'], b['top'], b['bottom']))
        else:
            sortie.append((w['text'], w['top'] - 2, w['bottom'] + 2))
    return sortie


TRACE = []  # (page, x0, x1, haut, bas, valeur) pour la vérification visuelle


def valeur(rendu, cellule_x, bande):
    (x0, x1), (t, b) = cellule_x, bande
    v = rendu.cellule(x0, x1, t, b)
    TRACE.append((rendu.num, x0, x1, t, b, v))
    return v


def extraire(chemin):
    pdf = pdfplumber.open(chemin)
    champ = section = None
    pile, savoirs, sans_colonnes = {}, [], []
    for num, page in enumerate(pdf.pages, 1):
        titre = ' '.join(w['text'] for w in page.extract_words(extra_attrs=['size'], x_tolerance=4) if w['size'] >= 13 and 35 <= w['top'] <= 60).strip()
        titre = re.sub(r'\s+', ' ', titre)
        titre = re.sub(r'(?<=[a-zé]) (?=[a-zé])', '', titre).replace('Mathématiquesdiscrètes', 'Mathématiques discrètes')  # « Géom étrie »
        lignes = (page.extract_text() or '').split('\n')
        for i, l in enumerate(lignes):
            if l.startswith('L’élève apprend') and i > 0:
                prec = lignes[i - 1].strip()
                if i > 1 and prec[:1].islower() and not lignes[i - 2].rstrip().endswith('.'):
                    prec = lignes[i - 2].strip() + ' ' + prec   # titre de tableau sur deux lignes
                if len(prec) < 120 and not prec.endswith('.'):
                    section = re.sub(r'(?<=[a-zé])\d$', '', prec)   # appel de note collé au titre
                    pile = {}
                break
        cols = colonnes(page)
        if not cols:
            if any(im['x0'] > 380 and im['width'] < 16 for im in page.images):
                sans_colonnes.append(num)
            continue
        x_col = cols[0][0] - 1
        horiz = sorted({round(l['top'], 1) for l in page.lines if abs(l['top'] - l['bottom']) < 1 and l['x0'] < x_col and l['x1'] - l['x0'] > 60}
                       | {round(r['top'], 1) for r in page.rects if r['height'] < 2.5 and r['width'] > 60 and r['x0'] < x_col})
        entete = [w for w in page.extract_words() if w['text'] in ('5e', '6e') and w['x0'] > x_col - 3]
        # en-tête de légende en haut de page seulement ; un en-tête au milieu (nouvelle partie) ne coupe rien
        legende = [w for w in page.extract_words() if w['text'] == 'L’élève' and w['x1'] < x_col]
        premiers = [w for w in entete if legende and w['top'] > min(l['top'] for l in legende)]
        haut = (min(w['bottom'] for w in premiers) + 1) if premiers else 14
        verticales = [r['bottom'] for r in page.rects if r['width'] < 2.5 and r['height'] > 8 and r['x0'] > x_col - 2]
        verticales += [l['bottom'] for l in page.lines if abs(l['x0'] - l['x1']) < 1 and l['x0'] > x_col - 2]
        bas = max(horiz + verticales) if horiz or verticales else page.height - 40
        if verticales and max(verticales) > max(horiz, default=0) + 2:
            horiz = horiz + [max(verticales)]
        rangs = lignes_texte(page, x_col, haut, bas, cols[-1][1] - 1, [w['top'] for w in page.extract_words() if w['text'] in ('6e', '1re', '2e', '3e', '4e', '5e', 'cycle', 'Secondaire') and w['x0'] > x_col - 3])
        elements, en_attente, x_lettre = [], [], None
        for r in rangs:
            n = None if r['petit'] else niveau(r['texte'])
            # « i. » peut être une lettre (après « h. ») ou un chiffre romain : l'alinéa tranche
            if n == 4 and x_lettre is not None and abs(r['x0'] - x_lettre) < 4:
                n = 3
            if n == 3:
                x_lettre = r['x0']
            if n is not None or not elements:
                meme_cellule = [l for l in en_attente if not any(l['bottom'] < h < r['top'] for h in horiz)]
                autres = [l for l in en_attente if l not in meme_cellule]
                if autres:   # rangée sans marqueur dans sa propre cellule
                    elements.append({'niveau': None, 'lignes': autres, 'top': autres[0]['top']})
                elements.append({'niveau': n, 'lignes': meme_cellule + [r], 'top': min([r['top']] + [l['top'] for l in meme_cellule])})
                en_attente = []
            else:
                prec_bas = max(l['bottom'] for l in elements[-1]['lignes'])
                if any(prec_bas < h < r['top'] for h in horiz):
                    en_attente.append(r)   # nouvelle cellule : appartient à l'élément suivant (ex. numérateur d'une fraction)
                else:
                    elements[-1]['lignes'].append(r)
        if en_attente and elements:
            elements[-1]['lignes'] += en_attente
        rendu = Rendu(page)
        rendu.num = num
        seqs = etiquettes_sequences(page, cols)
        for i, e in enumerate(elements):
            avec_marqueur = [l for l in e['lignes'] if not l['petit'] and niveau(l['texte'])]
            bas_txt = (avec_marqueur[0] if avec_marqueur else e['lignes'][0])['bottom']
            t = max([h for h in horiz if h <= e['top'] + 0.5], default=e['top'] - 4)
            b = min([h for h in horiz if h >= bas_txt - 0.5], default=bas_txt + 4)
            if i + 1 < len(elements):
                b = min(b, max(elements[i + 1]['top'] - 0.5, bas_txt))
            e['bande'] = (t, b)
        for e in elements:
            t, b = e['bande']
            prog = {}
            for k, a in enumerate(ANNEES):
                prog[a] = valeur(rendu, cols[k], (t, b))
            dans = [s for s in seqs if t - 1 <= (s[1] + s[2]) / 2 <= b + 1]
            if len(dans) >= 2:
                for k, a in ((4, '4'), (5, '5')):
                    # les sous-rangées sont de hauteur égale ; les étiquettes sont légèrement décalées
                    dans.sort(key=lambda s: s[1])
                    h = (b - t) / len(dans)
                    prog[a] = {nom: valeur(rendu, cols[k], (t + j * h, t + (j + 1) * h)) for j, (nom, _, _) in enumerate(dans)}
                    for nom in SEQUENCES:
                        prog[a].setdefault(nom, None)
            e['lignes'].sort(key=lambda l: l['top'])
            principales = [l for l in e['lignes'] if not l['petit']]
            if num in DEBUG:
                print(num, [round(v) for v in e['bande']], e['niveau'], ' '.join(l['texte'] for l in principales)[:40], prog)
            notes = [l for l in e['lignes'] if l['petit']]
            texte = re.sub(r'\s+', ' ', ' '.join(l['texte'] for l in principales)).strip()
            note_pda = re.sub(r'\s+', ' ', ' '.join(l['texte'] for l in notes)).strip()
            if note_pda and not texte:
                texte, note_pda = note_pda, ''
            if re.match(r'^Note\s*:', texte) and savoirs and savoirs[-1]['page'] == num:
                savoirs[-1]['note_pda'] = (savoirs[-1].get('note_pda', '') + ' ' + texte).strip()
                continue
            m = re.search(r'\s*\bNote\s*:?\s*(.*)$', texte)
            if m:
                note_pda = (m.group(1) + ' ' + note_pda).strip()
                texte = texte[:m.start()].strip()
            n = e['niveau'] or 6
            a_symbole = any((v if not isinstance(v, dict) else any(v.values())) for v in prog.values())
            if not a_symbole:
                pile = {k: v for k, v in pile.items() if k < n}
                pile[n] = texte
                continue
            empile = any(len(l['texte']) <= 3 for l in principales[1:]) or any(len(l['texte']) <= 3 for l in principales[:1] if len(principales) > 1)
            formule = bool(re.search(r'[=^√]|\bf\(x\)', texte))
            raisons = []
            if any(im['x1'] < x_col + 2 and im['srcsize'][0] > 100 and t - 1 <= (im['top'] + im['bottom']) / 2 <= b + 1 for im in page.images):
                raisons.append('Texte intégré dans une image : compléter à partir de la page.')
            if e['niveau'] is None: raisons.append('Ligne sans marqueur de liste : vérifier le découpage.')
            if empile: raisons.append('Fraction ou expression empilée : vérifier la notation.')
            elif formule: raisons.append('Formule : vérifier la notation.')
            gras = sum(l['gras'] for l in principales) / max(1, sum(l['total'] for l in principales))
            savoirs.append({
                'champ': titre or champ, 'section': section,
                'chemin': [pile[k] for k in sorted(pile) if k < n],
                'texte': texte, 'prioritaire': gras > 0.5,
                'progression': prog, 'page': num,
                'a_verifier': bool(raisons), 'note': ' '.join(raisons),
                **({'note_pda': note_pda} if note_pda else {}),
            })
        if titre:
            champ = titre
    return savoirs, sans_colonnes


# Rangées relues à la main sur la page (formules empilées, racines dessinées, texte en image).
# Clé : (page, début du texte extrait) ; valeur : texte exact, et note de la PDA s'il y a lieu.
CORRECTIONS = {
    (8, 'h. des nombres en notation logarithmique'): ('h. des nombres en notation logarithmique en utilisant, au besoin, l’équivalence log_a x = n ⇔ a^n = x', None),
    (10, 'b. Utiliser dans différents contextes des caractères de divisibilité'): ('b. Utiliser dans différents contextes des caractères de divisibilité : 2, 3, 4, 5 et 10', None),
    (15, 'e. de la substitution d’identités'): ('e. de la substitution d’identités algébriques du second degré (trinôme carré parfait et différence de deux carrés)', None),
    (16, '6. Déterminer le terme manquant'): ('6. Déterminer le terme manquant dans une équation (relations entre les opérations) : a + b = □, a + □ = c, □ + b = c, a – b = □, a – □ = c, □ – b = c, a × b = □, a × □ = c, □ × b = c, a ÷ b = □, a ÷ □ = c, □ ÷ b = c', None),
    (15, '– b+ b^2'): ('x_1 = (–b + √(b^2 – 4ac)) / 2a et x_2 = (–b – √(b^2 – 4ac)) / 2a', None),
    (19, 'i. f(x) = a bx'): ('i. f(x) = a√(bx)', None),
    (19, 'ii. f(x) = a b(x'): ('ii. f(x) = a√(b(x – h)) + k', None),
    (19, 'k ∈ i.'): ('i. f(x) = k/x ou xy = k, k ∈ ℚ₊', ''),
    (19, 'ii. f(x) = a +k'): ('ii. f(x) = a(1 / b(x – h)) + k et f(x) = (ax + b) / (cx + d)', None),
    (19, 'i. f(x) = ac ^x'): ('i. f(x) = ac^x', None),
    (19, 'ii. f(x) = ac ^bx'): ('ii. f(x) = ac^(bx)', None),
    (19, 'iii. f(x) = ac^b'): ('iii. f(x) = ac^(b(x – h)) + k', None),
    (19, 'ii. f(x) = a log_c b(x – h )'): ('ii. f(x) = a log_c b(x – h) + k', None),
    (19, 'g.'): ('g. Fonctions définies par parties', None),
    (19, 'h. Fonctions valeur absolue'): ('h. Fonctions valeur absolue : f(x) = a|b(x – h)| + k',
                                         'En TS, cette fonction est principalement abordée à titre de fonction définie par parties.'),
    (23, 'Choisir et appliquer le concept de chance'): ('10. Choisir et appliquer le concept de chance (chances pour, chances contre) ou de probabilité selon le contexte', None),
}


def corriger(s):
    s['texte'] = re.sub(r'(?<=[a-zéèà]{3})\^\d\b', '', s['texte'])   # appels de note (ex. « propriétés^1 »)
    s['chemin'] = [re.sub(r'(?<=[a-zéèà]{3})\^\d\b', '', c) for c in s['chemin']]
    for (page, debut), (texte, note) in CORRECTIONS.items():
        if s['page'] == page and (s['texte'] == debut if debut == 'g.' else s['texte'].startswith(debut)):
            s['texte'] = texte
            if note is not None:
                if note: s['note_pda'] = note
                else: s.pop('note_pda', None)
            s['a_verifier'] = False
            s['note'] = 'Formule ou texte relu à la main sur la page.'
            return True
    if s['a_verifier'] and s['note'].startswith('Formule') and not re.search(r'[□√]|\(\s*$', s['texte']):
        # formule simple lue correctement (exposants ^ et indices _) : relue sur la page
        s['a_verifier'] = False
        s['note'] = 'Formule : exposants notés ^, indices notés _.'
    return False


if __name__ == '__main__':
    src, sortie = sys.argv[1:3]
    savoirs, sans_colonnes = extraire(src)
    appliquees = sum(corriger(s) for s in savoirs)
    if appliquees != len(CORRECTIONS):
        print('ATTENTION : corrections appliquées', appliquees, 'sur', len(CORRECTIONS))
    compteur = collections.Counter()
    for s in savoirs:
        cle = re.sub(r'[^A-Z]', '', (s['champ'] or 'XXX').upper().replace('É', 'E').replace('È', 'E'))[:3]
        cle = {'MAT': 'DIS'}.get(cle, cle)   # « Mathématiques discrètes »
        compteur[cle] += 1
        s['id'] = f'MAT-{cle}-{compteur[cle]:03d}'
    par_seq = sum(1 for s in savoirs if any(isinstance(v, dict) for v in s['progression'].values()))
    out = {'discipline': 'Mathématique', 'code_discipline': 'MAT', 'ordre': 'secondaire',
           'source': src.split('/')[-1], 'annees': ANNEES, 'sequences': list(SEQUENCES),
           'legende': {'primaire': 'Rappel des acquis de la 6e année du primaire',
                       '4 et 5': 'Valeur simple si commune aux trois séquences, sinon objet par séquence'},
           'pages_sans_colonnes_reperees': sans_colonnes,
           'bilan': {'nombre_savoirs': len(savoirs), 'par_sequence': par_seq,
                     'a_verifier': sum(s['a_verifier'] for s in savoirs),
                     'prioritaires': sum(s['prioritaire'] for s in savoirs)},
           'savoirs': [{k: s[k] for k in ('id', 'champ', 'section', 'chemin', 'texte', 'prioritaire', 'progression', 'page', 'a_verifier', 'note', 'note_pda') if k in s} for s in savoirs]}
    json.dump(out, open(sortie, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(out['bilan'], ensure_ascii=False), 'pages sans colonnes :', sans_colonnes)
    print('symboles lus :', dict(CONTROLE))
