// Essais du coffre (maquettes/js/coffre.js) dans Node : mêmes API WebCrypto que le navigateur.
// Usage : node --test tests/coffre.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as K from '../maquettes/js/coffre.js';

const PHRASE = 'le lac Saint-Jean en octobre';

test('créer puis rouvrir le coffre avec la phrase secrète', async () => {
  const { maitre, code, envoi } = await K.creerCoffre(PHRASE);
  assert.match(code, /^[0-9A-Z]{4}(-[0-9A-Z]{1,4}){6}$/);
  assert.equal(envoi.iterations_phrase, 600000);
  const ct = await K.chiffrerTexte(maitre, 'Léa Gagnon', 'g1');
  const m2 = await K.ouvrirParPhrase(envoi, PHRASE);
  assert.equal(await K.dechiffrerTexte(m2, ct, 'g1'), 'Léa Gagnon');
  await assert.rejects(() => crypto.subtle.exportKey('raw', m2), 'la clé ouverte ne peut pas être exportée');
});

test('rien de lisible dans ce qui part au serveur', async () => {
  const { envoi } = await K.creerCoffre(PHRASE);
  const tout = JSON.stringify(envoi);
  assert.ok(!tout.includes('Saint-Jean') && !tout.includes(btoa('le lac')));
});

test('mauvaise phrase et mauvais code refusés', async () => {
  const { envoi } = await K.creerCoffre(PHRASE);
  await assert.rejects(K.ouvrirParPhrase(envoi, 'le lac Saint-Jean en novembre'), /phrase secrète incorrecte/);
  await assert.rejects(K.ouvrirParCode(envoi, 'AAAA-AAAA-AAAA-AAAA-AAAA-AAAA-AA'), /code de récupération incorrect/);
  await assert.rejects(K.ouvrirParCode(envoi, 'trop court'), /mal formé/);
  await assert.rejects(K.creerCoffre('court'), /12 caractères/);
});

test('phrase oubliée : le code imprimé rouvre le coffre et permet une nouvelle phrase', async () => {
  const { maitre, code, envoi } = await K.creerCoffre(PHRASE);
  const ct = await K.chiffrerTexte(maitre, 'Noah Bouchard', 'g1');
  const tape = code.toLowerCase().replace(/-/g, ' ').replace(/0/g, 'o');   // saisie imparfaite tolérée
  const m2 = await K.ouvrirParCode(envoi, tape);
  assert.equal(await K.dechiffrerTexte(m2, ct, 'g1'), 'Noah Bouchard');
  const neuf = await K.changerPhrase(envoi, (x) => K.ouvrirParCode(envoi, code, x), 'une toute nouvelle phrase');
  const m3 = await K.ouvrirParPhrase(neuf, 'une toute nouvelle phrase');
  assert.equal(await K.dechiffrerTexte(m3, ct, 'g1'), 'Noah Bouchard');
  await assert.rejects(K.ouvrirParPhrase(neuf, PHRASE), /incorrecte/);
  assert.ok(await K.ouvrirParCode(neuf, code), 'le code imprimé fonctionne toujours');
});

test('un nom copié dans un autre groupe ne se déchiffre pas', async () => {
  const g = await K.nouvelleCleGroupe();
  const ct = await K.chiffrerTexte(g, 'Léa Gagnon', 'groupe-A');
  await assert.rejects(K.dechiffrerTexte(g, ct, 'groupe-B'), /illisible/);
});

test('clé de groupe enveloppée par la clé maîtresse', async () => {
  const { maitre } = await K.creerCoffre(PHRASE);
  const g = await K.nouvelleCleGroupe();
  const env = await K.envelopperCleGroupe(g, maitre);
  const g2 = await K.ouvrirCleGroupe(env, maitre);
  assert.equal(await K.dechiffrerTexte(g2, await K.chiffrerTexte(g, '401', 'nom'), 'nom'), '401');
  const autre = await K.creerCoffre(PHRASE);
  await assert.rejects(K.ouvrirCleGroupe(env, autre.maitre));
});

test('partage d’un groupe avec une collègue (ECDH), sans que le serveur voie la clé', async () => {
  const titulaire = await K.creerCoffre(PHRASE);
  const collegue = await K.creerCoffre('une autre phrase bien longue');
  const intrus = await K.creerCoffre('la phrase de quelqu’un d’autre');
  const g = await K.nouvelleCleGroupe();
  const ct = await K.chiffrerTexte(g, 'Léa Gagnon', 'g1');
  const pourElle = await K.envelopperPour(g, collegue.clePublique);
  const recue = await K.ouvrirPartage(pourElle, collegue.envoi, collegue.maitre);
  assert.equal(await K.dechiffrerTexte(recue, ct, 'g1'), 'Léa Gagnon');
  await assert.rejects(K.ouvrirPartage(pourElle, intrus.envoi, intrus.maitre));
  // La collègue réenveloppe la clé avec sa propre clé maîtresse
  const sienne = await K.ouvrirCleGroupe(await K.envelopperCleGroupe(recue, collegue.maitre), collegue.maitre);
  assert.equal(await K.dechiffrerTexte(sienne, ct, 'g1'), 'Léa Gagnon');
});
