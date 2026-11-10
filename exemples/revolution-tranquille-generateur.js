const pptxgen = require('pptxgenjs');
const { applyTheme } = require('/root/.claude/skills/synced/3fed25c5-4b66-457d-aff3-b54301d14beb_36953556-435c-40ff-a000-041d82899917/pptx/scripts/apply_theme.js');
const THEME = { name: 'Carnet', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '33302B', lt1: 'FFFFFF', dk2: '7A726A', lt2: 'FAF7F1', accent1: 'B0704F', accent2: '55745D', accent3: '4F6F8F', accent4: 'C9A35F', accent5: 'E6DFD2', accent6: 'F6E4D8', hlink: '4F6F8F', folHlink: '7C6FA8' } };
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE'; pres.theme = { headFontFace: 'Cambria', bodyFontFace: 'Calibri' };
pres.title = 'La Révolution tranquille'; pres.author = 'Salle des profs';
const C = pres.SchemeColor; const W = 13.333;
const PIED = 'Histoire du Québec et du Canada · 4e secondaire';

pres.defineSlideMaster({ title: 'TITRE', background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: 'surtitre', type: 'body', x: 0.9, y: 1.6, w: 11, h: 0.5, fontSize: 16, color: C.accent4, charSpacing: 3, margin: 0 }, text: '' } },
    { placeholder: { options: { name: 'title', type: 'title', x: 0.9, y: 2.15, w: 11.5, h: 1.6, fontSize: 54, bold: true, color: C.background2, margin: 0, valign: 'top', align: 'left' }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.9, y: 3.9, w: 10.5, h: 1.4, fontSize: 20, color: C.accent5, margin: 0, valign: 'top' }, text: '' } },
  ] });
pres.defineSlideMaster({ title: 'CONTENU', background: { color: C.background2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontSize: 36, bold: true, color: C.text1, margin: 0, valign: 'middle' }, text: '' } },
    { text: { text: PIED, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.text2, margin: 0 } } },
  ], slideNumber: { x: 12.2, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.text2, align: 'right' } });
pres.defineSlideMaster({ title: 'SOMBRE', background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 12.1, h: 0.95, fontSize: 36, bold: true, color: C.background2, margin: 0, valign: 'middle' }, text: '' } },
    { text: { text: PIED, options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
  ], slideNumber: { x: 12.2, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent5, align: 'right' } });

let n = 0;
const nom = (s) => `${s}-${++n}`;
function carte(s, x, y, w, h, fill = C.background1) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill }, line: { color: C.accent5, width: 1 }, objectName: nom('carte') });
}
function rond(s, x, y, d, txt, fill = C.accent1, size = 16) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: nom('rond') });
  s.addText(txt, { x, y, w: d, h: d, fontSize: size, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0, isTextBox: true, objectName: nom('rond-texte') });
}
const T = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, valign: 'top', color: C.text1, fontSize: 16, objectName: nom('texte'), ...o });

// 1. Titre
pres.addSection({ title: 'Introduction' });
let s = pres.addSlide({ masterName: 'TITRE', sectionTitle: 'Introduction' });
s.addText('HISTOIRE DU QUÉBEC ET DU CANADA · 4E SECONDAIRE', { placeholder: 'surtitre' });
s.addText('La Révolution tranquille', { placeholder: 'title' });
s.addText('1960-1970 : l\'État québécois se transforme, et la société avec lui', { placeholder: 'body' });
rond(s, 0.9, 5.7, 0.55, '1960', C.accent1, 11); rond(s, 1.65, 5.7, 0.55, '1970', C.accent2, 11);
T(s, 'Période : 1945-1980, la modernisation du Québec et la Révolution tranquille', { x: 2.45, y: 5.78, w: 9, h: 0.45, fontSize: 14, color: C.accent5 });
s.addNotes("Objectif de la leçon : caractériser les principaux changements de la Révolution tranquille et se demander s'il s'agit d'une rupture ou de la suite d'une modernisation déjà en cours. Durée prévue : 20 à 25 minutes, puis les questions de la dernière diapositive.");

// 2. Avant 1960
pres.addSection({ title: 'Le contexte' });
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Le contexte' });
s.addText('Avant 1960 : un Québec conservateur ?', { placeholder: 'title' });
const avant = [['Le pouvoir politique', 'Maurice Duplessis (Union nationale) dirige le Québec de 1944 à 1959 : autonomie provinciale, méfiance envers Ottawa et les syndicats.'],
  ['Le rôle de l\'Église', 'L\'Église catholique dirige la plupart des écoles, des hôpitaux et des services sociaux.'],
  ['L\'économie', 'Le Québec s\'industrialise, mais les grandes entreprises appartiennent surtout à des capitaux anglophones et américains.']];
avant.forEach(([h, t], i) => { const y = 1.55 + i * 1.6; carte(s, 0.6, y, 7.1, 1.4); rond(s, 0.85, y + 0.38, 0.62, String(i + 1));
  T(s, h, { x: 1.7, y: y + 0.2, w: 5.8, h: 0.4, fontSize: 18, bold: true }); T(s, t, { x: 1.7, y: y + 0.6, w: 5.8, h: 0.75, fontSize: 14, color: C.text2 }); });
carte(s, 8.1, 1.55, 4.6, 4.6, C.accent6);
T(s, 'Des voix de contestation', { x: 8.4, y: 1.8, w: 4.1, h: 0.45, fontSize: 18, bold: true, color: C.accent1 });
T(s, [{ text: '1948 · Refus global', options: { bold: true, breakLine: true } }, { text: 'Des artistes dénoncent le conservatisme et l\'emprise de l\'Église.', options: { breakLine: true } },
  { text: ' ', options: { breakLine: true, fontSize: 8 } },
  { text: '1949 · Grève de l\'amiante', options: { bold: true, breakLine: true } }, { text: 'Les mineurs d\'Asbestos et de Thetford affrontent les compagnies et le gouvernement.' }],
  { x: 8.4, y: 2.35, w: 4.1, h: 2.6, fontSize: 14 });
T(s, 'Le terme « Grande Noirceur » est débattu par les historiens : le Québec se modernise déjà après 1945.', { x: 8.4, y: 5.0, w: 4.1, h: 1.0, fontSize: 13, italic: true, color: C.text2 });
s.addNotes("Insister sur la nuance : la période Duplessis n'est pas immobile. L'urbanisation et l'industrialisation progressent. On y reviendra à la diapositive « Rupture ou continuité ? ».");

// 3. 1960
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Le contexte' });
s.addText('1960 : « C\'est le temps que ça change »', { placeholder: 'title' });
T(s, '22 juin 1960', { x: 0.6, y: 1.8, w: 6, h: 1.2, fontSize: 60, bold: true, color: C.accent1, fontFace: 'Cambria' });
T(s, 'Le Parti libéral de Jean Lesage remporte les élections.', { x: 0.6, y: 3.05, w: 5.6, h: 0.9, fontSize: 20 });
T(s, 'Son slogan annonce une rupture avec l\'ère Duplessis.', { x: 0.6, y: 3.95, w: 5.6, h: 0.6, fontSize: 16, color: C.text2 });
const ev = [['Septembre 1959', 'Mort de Maurice Duplessis. Son successeur, Paul Sauvé, annonce des changements, mais meurt en janvier 1960.'],
  ['1960', 'Lesage forme « l\'équipe du tonnerre », dont René Lévesque et Paul Gérin-Lajoie.'],
  ['1962', 'Réélection sur le thème « Maîtres chez nous ».']];
ev.forEach(([d, t], i) => { const y = 1.7 + i * 1.6; carte(s, 6.9, y, 5.8, 1.4);
  T(s, d, { x: 7.2, y: y + 0.2, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: C.accent2 }); T(s, t, { x: 7.2, y: y + 0.6, w: 5.3, h: 0.75, fontSize: 14 }); });
s.addNotes("Le slogan de 1960 est « C'est le temps que ça change ». Celui de 1962, « Maîtres chez nous », porte sur la nationalisation de l'électricité.");

// 4. Ligne du temps
pres.addSection({ title: 'Les transformations' });
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Les transformations' });
s.addText('Une décennie de réformes', { placeholder: 'title' });
const tl = [['1960', 'Élection de Jean Lesage'], ['1961', 'Ministère des Affaires culturelles ; Office de la langue française'], ['1962', 'Société générale de financement'],
  ['1963', 'Nationalisation de l\'électricité : Hydro-Québec s\'agrandit'], ['1964', 'Ministère de l\'Éducation'], ['1965', 'Caisse de dépôt et placement ; Régime de rentes'],
  ['1967', 'Création des cégeps'], ['1968', 'Réseau de l\'Université du Québec']];
s.addShape(pres.shapes.RECTANGLE, { x: 1.3, y: 4.0, w: 10.75, h: 0.06, fill: { color: C.accent5 }, line: { color: C.accent5 }, objectName: 'axe' });
tl.forEach(([a, t], i) => { const x = 1.6 + i * 1.45; const haut = i % 2 === 0;
  s.addShape(pres.shapes.OVAL, { x: x - 0.14, y: 3.89, w: 0.28, h: 0.28, fill: { color: i % 2 ? C.accent2 : C.accent1 }, line: { color: C.background2, width: 2 }, objectName: nom('point') });
  T(s, a, { x: x - 0.6, y: haut ? 3.3 : 4.3, w: 1.2, h: 0.45, fontSize: 18, bold: true, align: 'center', color: i % 2 ? C.accent2 : C.accent1, fontFace: 'Cambria', valign: haut ? 'bottom' : 'top' });
  T(s, t, { x: x - 1.1, y: haut ? 2.55 : 4.8, w: 2.2, h: 0.75, fontSize: 14, align: 'center', valign: haut ? 'bottom' : 'top' }); });
s.addNotes("Faire remarquer aux élèves que l'État crée des institutions qui existent encore aujourd'hui. Demander lesquelles ils connaissent (Hydro-Québec, cégeps, Caisse de dépôt).");

// 5. Etat vs Eglise
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Les transformations' });
s.addText('L\'État remplace l\'Église', { placeholder: 'title' });
const col = [['Éducation', 'Les communautés religieuses et les commissions scolaires confessionnelles dirigent les écoles.', 'Rapport Parent (1963-1966), ministère de l\'Éducation (1964), polyvalentes, cégeps (1967) : l\'école devient accessible à tous.'],
  ['Santé', 'Les hôpitaux appartiennent surtout à des communautés religieuses ; les soins coûtent cher.', 'Assurance-hospitalisation (1961) : l\'État paie les soins à l\'hôpital. L\'assurance-maladie suivra en 1970.'],
  ['Services sociaux', 'La charité et les œuvres religieuses aident les plus pauvres.', 'L\'État crée des programmes : Régime de rentes du Québec (1965), aide sociale.']];
T(s, 'AVANT', { x: 3.35, y: 1.5, w: 4.4, h: 0.35, fontSize: 13, bold: true, color: C.text2, charSpacing: 2 });
T(s, 'APRÈS', { x: 8.2, y: 1.5, w: 4.5, h: 0.35, fontSize: 13, bold: true, color: C.accent2, charSpacing: 2 });
col.forEach(([h, a, b], i) => { const y = 1.95 + i * 1.6;
  T(s, h, { x: 0.6, y: y + 0.45, w: 2.5, h: 0.5, fontSize: 20, bold: true, fontFace: 'Cambria' });
  carte(s, 3.2, y, 4.6, 1.4); T(s, a, { x: 3.45, y: y + 0.18, w: 4.1, h: 1.1, fontSize: 14, color: C.text2 });
  carte(s, 8.05, y, 4.65, 1.4, C.accent6); T(s, b, { x: 8.3, y: y + 0.18, w: 4.2, h: 1.1, fontSize: 14 }); });
s.addNotes("Concept clé : l'État-providence. L'État prend en charge l'éducation, la santé et les services sociaux, qui relevaient surtout de l'Église. C'est aussi le début de la laïcisation des institutions.");

// 6. Maitres chez nous
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Les transformations' });
s.addText('« Maîtres chez nous » : l\'économie', { placeholder: 'title' });
carte(s, 0.6, 1.55, 5.3, 4.95, C.text1);
T(s, 'Le but', { x: 0.95, y: 1.85, w: 4.6, h: 0.45, fontSize: 16, bold: true, color: C.accent4 });
T(s, 'Donner aux Québécois francophones le contrôle de leur économie, alors dominée par des capitaux étrangers et anglophones.', { x: 0.95, y: 2.35, w: 4.6, h: 1.8, fontSize: 18, color: C.background2 });
T(s, 'L\'outil : l\'État québécois et ses sociétés d\'État.', { x: 0.95, y: 4.4, w: 4.6, h: 1.0, fontSize: 16, italic: true, color: C.accent5 });
const eco = [['Hydro-Québec, 1963', 'Sous René Lévesque, ministre des Richesses naturelles, l\'État achète les compagnies privées d\'électricité.'],
  ['Société générale de financement, 1962', 'Elle investit dans des entreprises québécoises.'],
  ['Caisse de dépôt et placement, 1965', 'Elle gère l\'épargne collective, dont les cotisations au Régime de rentes, et l\'investit au Québec.']];
eco.forEach(([h, t], i) => { const y = 1.55 + i * 1.7; carte(s, 6.3, y, 6.4, 1.5); rond(s, 6.55, y + 0.42, 0.66, String(i + 1), C.accent2);
  T(s, h, { x: 7.45, y: y + 0.22, w: 5.05, h: 0.4, fontSize: 17, bold: true }); T(s, t, { x: 7.45, y: y + 0.65, w: 5.05, h: 0.8, fontSize: 14, color: C.text2 }); });
s.addNotes("La nationalisation de l'électricité est le grand enjeu de l'élection de 1962. Elle devient le symbole de la Révolution tranquille.");

// 7. Societe
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Les transformations' });
s.addText('Une société qui change', { placeholder: 'title' });
const soc = [['Laïcisation', 'La pratique religieuse diminue rapidement. Les institutions publiques ne dépendent plus de l\'Église.', C.accent1],
  ['Les femmes', '1961 : Claire Kirkland-Casgrain, première femme élue à l\'Assemblée législative. 1964 : la loi 16 donne la capacité juridique à la femme mariée.', C.accent2],
  ['La culture', '1961 : ministère des Affaires culturelles. La chanson, le théâtre et la littérature québécoises s\'affirment.', C.accent3],
  ['La langue', '1961 : Office de la langue française. La place du français devient un enjeu politique.', C.accent4]];
soc.forEach(([h, t, c], i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.55; carte(s, x, y, 5.95, 2.3);
  s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.32, w: 0.42, h: 0.42, fill: { color: c }, line: { color: c }, objectName: nom('pastille') });
  T(s, h, { x: x + 0.9, y: y + 0.3, w: 4.8, h: 0.45, fontSize: 19, bold: true }); T(s, t, { x: x + 0.3, y: y + 0.95, w: 5.4, h: 1.25, fontSize: 14, color: C.text2 }); });
s.addNotes("Faire le lien avec la vie des élèves : école laïque, droits des femmes, place du français. Ces changements ont commencé pendant la Révolution tranquille.");

// 8. Nationalisme
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Les transformations' });
s.addText('Du Canadien français au Québécois', { placeholder: 'title' });
T(s, 'Un nouveau nationalisme', { x: 0.6, y: 1.6, w: 5.6, h: 0.45, fontSize: 20, bold: true, color: C.accent1, fontFace: 'Cambria' });
T(s, [{ text: 'L\'identité se centre sur le territoire du Québec et sur l\'État québécois.', options: { bullet: true, breakLine: true } },
  { text: 'Le Québec réclame plus de pouvoirs face au gouvernement fédéral.', options: { bullet: true, breakLine: true } },
  { text: 'L\'idée d\'indépendance gagne des appuis, surtout chez les jeunes.', options: { bullet: true } }],
  { x: 0.6, y: 2.2, w: 5.6, h: 2.6, fontSize: 16, paraSpaceAfter: 10 });
T(s, 'Le FLQ, groupe armé, commet des attentats à partir de 1963. La grande majorité des souverainistes rejettent la violence.', { x: 0.6, y: 5.0, w: 5.6, h: 1.0, fontSize: 13, italic: true, color: C.text2 });
const sv = [['1960', 'Rassemblement pour l\'indépendance nationale (RIN)'], ['1967', 'René Lévesque fonde le Mouvement souveraineté-association'], ['1968', 'Fondation du Parti québécois']];
sv.forEach(([a, t], i) => { const y = 1.6 + i * 1.55; carte(s, 6.8, y, 5.9, 1.35); rond(s, 7.05, y + 0.27, 0.8, a, C.accent3, 14);
  T(s, t, { x: 8.1, y: y + 0.3, w: 4.4, h: 0.8, fontSize: 16, valign: 'middle' }); });
s.addNotes("Expliquer le passage de l'identité canadienne-française (tout le Canada) à l'identité québécoise (le territoire du Québec). Mentionner que les débats constitutionnels avec Ottawa s'intensifient.");

// 9. Rupture ou continuité
pres.addSection({ title: 'Interpréter' });
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Interpréter' });
s.addText('Rupture ou continuité ?', { placeholder: 'title' });
T(s, 'Les historiens ne s\'entendent pas tous. Deux lectures de la Révolution tranquille :', { x: 0.6, y: 1.45, w: 12.1, h: 0.5, fontSize: 16, color: C.text2 });
const lect = [['Une rupture', C.accent1, ['Changements rapides en quelques années', 'L\'État remplace l\'Église dans l\'éducation et la santé', 'Nouvelles institutions, nouvelle identité']],
  ['Une continuité', C.accent2, ['L\'industrialisation et l\'urbanisation progressent depuis longtemps', 'Des critiques s\'expriment dès les années 1940 et 1950', 'Certaines réformes étaient déjà préparées avant 1960']]];
lect.forEach(([h, c, items], i) => { const x = 0.6 + i * 6.15; carte(s, x, 2.15, 5.95, 3.9);
  s.addShape(pres.shapes.OVAL, { x: x + 0.35, y: 2.45, w: 0.45, h: 0.45, fill: { color: c }, line: { color: c }, objectName: nom('pastille') });
  T(s, h, { x: x + 1.0, y: 2.43, w: 4.7, h: 0.5, fontSize: 22, bold: true, fontFace: 'Cambria', color: c });
  T(s, items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), { x: x + 0.4, y: 3.2, w: 5.2, h: 2.6, fontSize: 16, paraSpaceAfter: 10 }); });
T(s, 'Et vous ? Les deux lectures peuvent-elles être vraies en même temps ?', { x: 0.6, y: 6.25, w: 12.1, h: 0.45, fontSize: 16, italic: true, color: C.accent1 });
s.addNotes("Cette diapositive prépare la compétence Interpréter une réalité sociale. On peut faire voter la classe, puis demander des arguments appuyés sur les diapositives précédentes.");

// 10. A retenir
s = pres.addSlide({ masterName: 'CONTENU', sectionTitle: 'Interpréter' });
s.addText('À retenir', { placeholder: 'title' });
const ret = [['L\'État prend le relais', 'L\'État québécois remplace l\'Église dans l\'éducation, la santé et les services sociaux.'],
  ['« Maîtres chez nous »', 'Les sociétés d\'État, dont Hydro-Québec, visent à donner aux francophones le contrôle de leur économie.'],
  ['Une société transformée', 'Laïcisation, droits des femmes, affirmation de la culture et de la langue françaises.'],
  ['Une nouvelle identité', 'Du Canadien français au Québécois ; naissance du mouvement souverainiste moderne.']];
ret.forEach(([h, t], i) => { const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.55; carte(s, x, y, 5.95, 2.3);
  rond(s, x + 0.3, y + 0.3, 0.7, String(i + 1)); T(s, h, { x: x + 1.2, y: y + 0.4, w: 4.5, h: 0.5, fontSize: 19, bold: true });
  T(s, t, { x: x + 0.3, y: y + 1.15, w: 5.4, h: 1.0, fontSize: 15, color: C.text2 }); });
s.addNotes("Résumé en quatre idées. On peut demander aux élèves de les recopier dans leur cahier avec un exemple pour chacune.");

// 11. Questions
s = pres.addSlide({ masterName: 'SOMBRE', sectionTitle: 'Interpréter' });
s.addText('À votre tour', { placeholder: 'title' });
const q = [['Déterminer des changements et des continuités', 'Nommez un changement et une continuité dans le domaine de l\'éducation entre 1950 et 1970.'],
  ['Déterminer des causes et des conséquences', 'Pourquoi le gouvernement Lesage nationalise-t-il l\'électricité ? Nommez une conséquence pour le Québec.'],
  ['Compétence 2 : interpréter une réalité sociale', 'La Révolution tranquille est-elle une rupture ou une continuité ? Appuyez votre réponse sur deux faits.']];
q.forEach(([h, t], i) => { const y = 1.6 + i * 1.7; rond(s, 0.6, y + 0.1, 0.75, String(i + 1), C.accent1, 18);
  T(s, h.toUpperCase(), { x: 1.65, y: y, w: 10.9, h: 0.4, fontSize: 13, bold: true, color: C.accent4, charSpacing: 1 });
  T(s, t, { x: 1.65, y: y + 0.45, w: 10.9, h: 0.9, fontSize: 20, color: C.background2 }); });
s.addNotes("Les deux premières questions reprennent des opérations intellectuelles du cadre d'évaluation ; la troisième relève de la compétence 2. La troisième peut devenir un court texte argumentatif.");

(async () => { await pres.writeFile({ fileName: 'revolution-tranquille-hqc-sec4.pptx' }); await applyTheme('revolution-tranquille-hqc-sec4.pptx', THEME); console.log('ok'); })();
