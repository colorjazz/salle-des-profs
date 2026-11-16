// Salle des profs · le coffre (spécification, section 5).
// Tout se passe dans le navigateur, avec WebCrypto : le serveur ne reçoit que des clés enveloppées
// et des textes chiffrés. Ni la phrase secrète, ni le code de récupération, ni un nom d'élève ne le quittent.
//
//   Clé maîtresse ........ AES-GCM 256, propre à l'enseignante
//   Phrase secrète ....... PBKDF2-SHA256, 600 000 itérations, enveloppe la clé maîtresse
//   Code de récupération . 128 bits aléatoires (26 caractères), HKDF, enveloppe aussi la clé maîtresse
//   Clé de groupe ........ AES-GCM 256, chiffre les noms ; enveloppée par la clé maîtresse de chaque membre
//   Partage .............. ECDH P-256 éphémère : la clé de groupe est enveloppée pour la clé publique d'une collègue
//
// Fonctionne aussi dans Node 20+ (mêmes API), ce qui permet les essais automatiques.

const c = globalThis.crypto.subtle;
const ITERATIONS = 600000;
const enc = new TextEncoder(), dec = new TextDecoder();
const ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';   // base 32 de Crockford : sans I, L, O ni U

const b64 = (o) => { let s = ''; new Uint8Array(o).forEach((x) => (s += String.fromCharCode(x))); return btoa(s); };
const octets = (s) => Uint8Array.from(atob(s), (x) => x.charCodeAt(0));
const hasard = (n) => globalThis.crypto.getRandomValues(new Uint8Array(n));
const joindre = (a, b) => { const r = new Uint8Array(a.length + b.length); r.set(a); r.set(b, a.length); return r; };

export class ErreurCoffre extends Error {}

// ───────────── Clés dérivées ─────────────

async function cleDePhrase(phrase, sel, iterations = ITERATIONS) {
  const base = await c.importKey('raw', enc.encode(phrase.normalize('NFC')), 'PBKDF2', false, ['deriveKey']);
  return c.deriveKey({ name: 'PBKDF2', hash: 'SHA-256', salt: sel, iterations }, base, { name: 'AES-GCM', length: 256 }, false, ['wrapKey', 'unwrapKey']);
}

async function cleDeCode(code) {
  const brut = decoderCode(code);
  const base = await c.importKey('raw', brut, 'HKDF', false, ['deriveKey']);
  return c.deriveKey({ name: 'HKDF', hash: 'SHA-256', salt: enc.encode('salle-des-profs/recuperation'), info: new Uint8Array() },
    base, { name: 'AES-GCM', length: 256 }, false, ['wrapKey', 'unwrapKey']);
}

// Enveloppe = iv (12 octets) + clé chiffrée. Le contexte (AAD) empêche de réutiliser une enveloppe ailleurs.
async function envelopper(cle, kek, contexte) {
  const iv = hasard(12);
  const w = await c.wrapKey('raw', cle, kek, { name: 'AES-GCM', iv, additionalData: enc.encode(contexte) });
  return joindre(iv, new Uint8Array(w));
}

async function desenvelopper(env, kek, contexte, extractible = false) {
  try {
    return await c.unwrapKey('raw', env.slice(12), kek, { name: 'AES-GCM', iv: env.slice(0, 12), additionalData: enc.encode(contexte) },
      { name: 'AES-GCM', length: 256 }, extractible, ['encrypt', 'decrypt', 'wrapKey', 'unwrapKey']);
  } catch {
    throw new ErreurCoffre('clé incorrecte');
  }
}

// ───────────── Code de récupération ─────────────

function encoderCode(o) {
  let bits = 0, n = 0, s = '';
  for (const x of o) { n = (n << 8) | x; bits += 8; while (bits >= 5) { s += ALPHABET[(n >> (bits - 5)) & 31]; bits -= 5; } }
  if (bits) s += ALPHABET[(n << (5 - bits)) & 31];
  return s.match(/.{1,4}/g).join('-');
}

function decoderCode(code) {
  const s = String(code).toUpperCase().replace(/[\s-]/g, '').replace(/O/g, '0').replace(/[IL]/g, '1');
  if (s.length !== 26 || [...s].some((x) => !ALPHABET.includes(x))) throw new ErreurCoffre('code de récupération mal formé');
  const r = []; let bits = 0, n = 0;
  for (const x of s) { n = ((n << 5) | ALPHABET.indexOf(x)) & 0xffff; bits += 5; if (bits >= 8) { r.push((n >> (bits - 8)) & 255); bits -= 8; } }
  return new Uint8Array(r.slice(0, 16));
}

// ───────────── Le coffre ─────────────

const VERIF = 'salle-des-profs:coffre:v1';

/** Crée le coffre à la première connexion. Retourne la clé maîtresse (à garder en mémoire seulement),
 *  le code de récupération (à imprimer, affiché une seule fois) et ce qu'il faut envoyer à PUT /api/coffre. */
export async function creerCoffre(phrase) {
  verifierPhrase(phrase);
  const maitre = await c.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt', 'wrapKey', 'unwrapKey']);
  const sel = hasard(16);
  const brutCode = hasard(16);
  const code = encoderCode(brutCode);
  const echange = await c.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveKey']);
  const envoi = {
    cle_par_phrase: b64(await envelopper(maitre, await cleDePhrase(phrase, sel), 'phrase')),
    sel_phrase: b64(sel),
    iterations_phrase: ITERATIONS,
    cle_par_recuperation: b64(await envelopper(maitre, await cleDeCode(code), 'recuperation')),
    verificateur: await chiffrerTexte(maitre, VERIF, 'verificateur'),
    cle_privee_ecdh: await chiffrerTexte(maitre, JSON.stringify(await c.exportKey('jwk', echange.privateKey)), 'ecdh'),
  };
  const clePublique = await c.exportKey('jwk', echange.publicKey);
  return { maitre: await rendreNonExportable(maitre), code, envoi, clePublique: { kty: 'EC', crv: 'P-256', x: clePublique.x, y: clePublique.y } };
}

/** Ouvre le coffre avec la phrase secrète (réponse de GET /api/coffre). */
export async function ouvrirParPhrase(coffre, phrase, extractible = false) {
  const kek = await cleDePhrase(phrase, octets(coffre.sel_phrase), coffre.iterations_phrase);
  const maitre = await desenvelopper(octets(coffre.cle_par_phrase), kek, 'phrase', extractible).catch(() => { throw new ErreurCoffre('phrase secrète incorrecte'); });
  await verifier(maitre, coffre);
  return maitre;
}

/** Ouvre le coffre avec le code de récupération imprimé (phrase oubliée). */
export async function ouvrirParCode(coffre, code, extractible = false) {
  const maitre = await desenvelopper(octets(coffre.cle_par_recuperation), await cleDeCode(code), 'recuperation', extractible)
    .catch((e) => { throw e.message.includes('mal formé') ? e : new ErreurCoffre('code de récupération incorrect'); });
  await verifier(maitre, coffre);
  return maitre;
}

/** Change la phrase secrète (après une ouverture par l'ancienne phrase ou par le code). Retourne les champs à renvoyer. */
export async function changerPhrase(coffre, ouvrir, nouvelle) {
  verifierPhrase(nouvelle);
  const maitre = await ouvrir(true);
  const sel = hasard(16);
  return { ...coffre, cle_par_phrase: b64(await envelopper(maitre, await cleDePhrase(nouvelle, sel), 'phrase')), sel_phrase: b64(sel), iterations_phrase: ITERATIONS };
}

async function verifier(maitre, coffre) {
  if ((await dechiffrerTexte(maitre, coffre.verificateur, 'verificateur')) !== VERIF) throw new ErreurCoffre('coffre incohérent');
}

function verifierPhrase(p) {
  if (typeof p !== 'string' || p.normalize('NFC').length < 12) throw new ErreurCoffre('la phrase secrète doit compter au moins 12 caractères');
}

async function rendreNonExportable(cle) {
  return c.importKey('raw', await c.exportKey('raw', cle), { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt', 'wrapKey', 'unwrapKey']);
}

// ───────────── Chiffrement des textes (noms d'élèves, nom du groupe) ─────────────

/** Chiffre un texte. Le contexte (ex. l'identifiant du groupe) lie le texte chiffré à sa place :
 *  un nom copié dans un autre groupe ne se déchiffre pas. */
export async function chiffrerTexte(cle, texte, contexte) {
  const iv = hasard(12);
  const ct = await c.encrypt({ name: 'AES-GCM', iv, additionalData: enc.encode(contexte) }, cle, enc.encode(texte));
  return b64(joindre(iv, new Uint8Array(ct)));
}

export async function dechiffrerTexte(cle, chiffre, contexte) {
  const o = octets(chiffre);
  try {
    return dec.decode(await c.decrypt({ name: 'AES-GCM', iv: o.slice(0, 12), additionalData: enc.encode(contexte) }, cle, o.slice(12)));
  } catch {
    throw new ErreurCoffre('texte illisible avec cette clé');
  }
}

// ───────────── Clés de groupe ─────────────

export const nouvelleCleGroupe = () => c.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);

export async function envelopperCleGroupe(cleGroupe, maitre) {
  return b64(await envelopper(cleGroupe, maitre, 'groupe'));
}

export async function ouvrirCleGroupe(enveloppe, maitre) {
  const k = await desenvelopper(octets(enveloppe), maitre, 'groupe', true);
  return k;
}

// ───────────── Partage d'un groupe avec une collègue ─────────────

async function cleEchange(privee, publique) {
  const brut = await c.deriveKey({ name: 'ECDH', public: publique }, privee, { name: 'AES-GCM', length: 256 }, false, ['wrapKey', 'unwrapKey']);
  return brut;
}

/** Enveloppe la clé d'un groupe pour une collègue, à partir de sa clé publique (profil). */
export async function envelopperPour(cleGroupe, clePubliqueCollegue) {
  const publique = await c.importKey('jwk', { ...clePubliqueCollegue, ext: true }, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const eph = await c.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveKey']);
  const w = await envelopper(cleGroupe, await cleEchange(eph.privateKey, publique), 'partage');
  const e = await c.exportKey('jwk', eph.publicKey);
  return btoa(JSON.stringify({ e: { kty: 'EC', crv: 'P-256', x: e.x, y: e.y }, w: b64(w) }));
}

/** La collègue ouvre la clé partagée avec sa propre clé privée (tirée de son coffre). */
export async function ouvrirPartage(enveloppe, coffre, maitre) {
  const { e, w } = JSON.parse(atob(enveloppe));
  const jwk = JSON.parse(await dechiffrerTexte(maitre, coffre.cle_privee_ecdh, 'ecdh'));
  const privee = await c.importKey('jwk', jwk, { name: 'ECDH', namedCurve: 'P-256' }, false, ['deriveKey']);
  const publique = await c.importKey('jwk', { ...e, ext: true }, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  return desenvelopper(octets(w), await cleEchange(privee, publique), 'partage', true);
}
