// Étape 4 du circuit Création : la réponse validée (2-reponse.json) devient un fichier Word.
// Dans l'application, ce rendu se fait dans le navigateur ; ici, avec Node et la même bibliothèque (docx).
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
        AlignmentType, Footer, PageNumber, PageBreak, TabStopType } = require('docx');

const ici = __dirname;
const r = JSON.parse(fs.readFileSync(path.join(ici, '2-reponse.json'), 'utf8'));
const d = JSON.parse(fs.readFileSync(path.join(ici, '1-demande.json'), 'utf8'));
const insecable = (c) => c.replace(/-/g, '\u2011');  // les codes ne se coupent pas en fin de ligne
const ENCRE = '33302B', DOUX = '7A726A', TERRE = 'B0704F', LIGNE = 'D9D1C3', FOND = 'F6F2EA';
const POLICE = 'Calibri';
const LARGEUR = 9360;  // Lettre, marges de 1 po : 12240 - 2 × 1440

const t = (texte, o = {}) => new TextRun({ text: texte, font: POLICE, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color || ENCRE });
const p = (enfants, o = {}) => new Paragraph({ children: Array.isArray(enfants) ? enfants : [enfants], spacing: { before: o.before || 0, after: o.after ?? 120, line: o.line || 276 }, alignment: o.align, keepNext: o.keepNext, tabStops: o.tabs, border: o.border });
const sansBord = { top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, bottom: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' } };
const bordFin = { style: BorderStyle.SINGLE, size: 4, color: LIGNE };
// Lignes d'écriture : un tableau (des paragraphes voisins à bordure identique seraient fusionnés par Word)
const lignesEcriture = (n) => new Table({ width: { size: LARGEUR, type: WidthType.DXA }, columnWidths: [LARGEUR],
  rows: Array.from({ length: n }, () => new TableRow({ height: { value: 400, rule: 'atLeast' }, children: [new TableCell({ children: [new Paragraph({ children: [] })],
    width: { size: LARGEUR, type: WidthType.DXA }, borders: { top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, bottom: { style: BorderStyle.SINGLE, size: 4, color: 'B9B0A2' } } })] })) });

function cellule(enfants, largeur, o = {}) {
  return new TableCell({ children: enfants, width: { size: largeur, type: WidthType.DXA }, borders: o.borders || sansBord,
    shading: o.fond ? { fill: o.fond, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: o.marge ?? 80, bottom: o.marge ?? 80, left: 140, right: 140 } });
}
function tableau(lignes, colonnes, o = {}) {
  return new Table({ width: { size: colonnes.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: colonnes, rows: lignes });
}

// En-tête de la fiche : école et matière à gauche, identification de l'élève à droite
const entete = tableau([new TableRow({ children: [
  cellule([p([t('École des Érables', { bold: true, size: 20 })], { after: 0 }), p([t(`${d.discipline.nom} · ${d.niveau.libelle}`, { size: 18, color: DOUX })], { after: 0 })], 5200),
  cellule([p([t('Nom : ______________________', { size: 20 })], { after: 60, align: AlignmentType.RIGHT }), p([t('Groupe : ________   Date : ____________', { size: 20 })], { after: 0, align: AlignmentType.RIGHT })], 4160),
] })], [5200, 4160]);

const corps = [
  entete,
  p([t(' ')], { after: 60, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: TERRE, space: 4 } } }),
  p([t(r.titre, { size: 40, bold: true })], { before: 200, after: 40 }),
  p([t(r.sous_titre, { size: 22, color: DOUX })], { after: 160 }),
  p([t('Intention : ', { bold: true, size: 20 }), t(r.intention, { size: 20 })], { after: 60 }),
  p([t('Durée : ', { bold: true, size: 20 }), t(r.duree, { size: 20 }), t('     Concept : ', { bold: true, size: 20 }), t(r.concept, { size: 20 }), t(`     Total : ${r.total} points`, { bold: true, size: 20 })], { after: 240 }),
];

// Documents
for (const doc of r.documents) {
  const contenu = [p([t(doc.titre, { bold: true, size: 22 })], { after: 40, keepNext: true }), p([t(doc.nature, { italics: true, size: 18, color: DOUX })], { after: 100, keepNext: true })];
  if (doc.texte) doc.texte.forEach(x => contenu.push(p([t(x, { size: 21 })], { after: 100 })));
  if (doc.listes) {
    const largeurs = [4400, 4400];
    contenu.push(tableau([new TableRow({ children: doc.listes.map((l, i) => cellule([
      p([t(l.titre, { bold: true, size: 19 })], { after: 80 }),
      ...l.elements.map(e => p([t('– ' + e, { size: 21 })], { after: 40 })),
    ], largeurs[i], { marge: 40 })) })], largeurs));
  }
  corps.push(tableau([new TableRow({ children: [cellule(contenu, LARGEUR, { fond: FOND, marge: 140, borders: { top: bordFin, bottom: bordFin, left: { style: BorderStyle.SINGLE, size: 18, color: TERRE }, right: bordFin } })] })], [LARGEUR]));
  corps.push(p([t(' ')], { after: 60 }));
}

// Questions
corps.push(p([t('Questions', { size: 30, bold: true })], { before: 120, after: 120, keepNext: true }));
for (const q of r.questions) {
  corps.push(p([t(q.operation.toUpperCase(), { size: 16, bold: true, color: TERRE })], { before: 140, after: 20, keepNext: true }));
  corps.push(p([t(`${q.numero}. `, { bold: true }), t(q.consigne), t(`\t${q.points} pts`, { size: 18, color: DOUX })],
    { after: 80, keepNext: true, tabs: [{ type: TabStopType.RIGHT, position: LARGEUR }] }));
  corps.push(lignesEcriture(q.lignes));
}

// Corrigé, sur une nouvelle page
corps.push(new Paragraph({ pageBreakBefore: true, spacing: { after: 60 }, children: [t('Corrigé · pour l’enseignant', { size: 30, bold: true })] }));
corps.push(p([t(`${r.titre} · ${d.niveau.libelle}`, { color: DOUX, size: 20 })], { after: 60 }));
corps.push(p([t('Faits tirés uniquement du texte officiel du programme (réalité sociale de la période). À relire avant l’impression.', { italics: true, size: 18, color: DOUX })], { after: 160 }));
const lc = [700, 2200, 5560, 900];
const enTete = new TableRow({ tableHeader: true, children: ['N°', 'Opération', 'Réponse attendue', 'Points'].map((x, i) =>
  cellule([p([t(x, { bold: true, size: 18, color: DOUX })], { after: 0 })], lc[i], { borders: { top: sansBord.top, left: sansBord.left, right: sansBord.right, bottom: bordFin } })) });
const lignesC = r.questions.map(q => new TableRow({ children: [
  cellule([p([t(String(q.numero), { bold: true, size: 20 })], { after: 0 })], lc[0], { borders: { ...sansBord, bottom: bordFin } }),
  cellule([p([t(q.operation, { size: 18 })], { after: 0 }), p([t(q.savoirs.map(insecable).join(', '), { size: 16, color: DOUX })], { after: 0 })], lc[1], { borders: { ...sansBord, bottom: bordFin } }),
  cellule([p([t(q.corrige, { size: 20 })], { after: 0 })], lc[2], { borders: { ...sansBord, bottom: bordFin } }),
  cellule([p([t(String(q.points), { size: 20 })], { after: 0, align: AlignmentType.CENTER })], lc[3], { borders: { ...sansBord, bottom: bordFin } }),
] }));
corps.push(tableau([enTete, ...lignesC], lc));
corps.push(p([t('Critères d’évaluation du programme (cadre d’évaluation)', { bold: true, size: 22 })], { before: 280, after: 80 }));
d.criteres.forEach(c => corps.push(p([t('– ' + c, { size: 20 })], { after: 40 })));
corps.push(p([t('Savoirs de la Progression des apprentissages travaillés', { bold: true, size: 22 })], { before: 180, after: 60 }));
corps.push(p(d.savoirs.flatMap((s, i) => [t((i ? '   ' : '') + insecable(s.id) + '\u00a0', { size: 17, color: DOUX }), t(s.texte, { size: 19 })]), { after: 0 }));

const pied = new Footer({ children: [p([
  t(`${d.discipline.nom} · ${d.niveau.libelle} · Créé avec Salle des profs`, { size: 16, color: DOUX }),
  new TextRun({ children: ['\t', PageNumber.CURRENT], font: POLICE, size: 16, color: DOUX }),
], { after: 0, tabs: [{ type: TabStopType.RIGHT, position: LARGEUR }] })] });

const document = new Document({
  creator: 'Salle des profs', title: r.titre, description: 'Fiche d’exercices produite à partir des données du programme',
  styles: { default: { document: { run: { font: POLICE, size: 22 } } } },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 } } },
               footers: { default: pied }, children: corps }],
});
Packer.toBuffer(document).then(b => { const f = path.join(ici, 'fiche-hqc-sec3-premiers-occupants.docx'); fs.writeFileSync(f, b); console.log('écrit', f); });
