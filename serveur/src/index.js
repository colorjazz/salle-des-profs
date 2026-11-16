// Salle des profs 2.0 · Worker (jalons J1 et J2 : socle, comptes, coffre, groupes).
// Les pages statiques sont servies par [assets] ; ce code ne reçoit que /api/*.
import { json, ErreurHttp } from './entetes.js';
import { verifierJeton } from './jeton.js';
import { connexion, commeEnseignante, ouvrirSession, versOctets, versB64 } from './base.js';

const NIVEAUX = new Set(['1', '2', '3', '4', '5', '6', 'sec1', 'sec2', 'sec3', 'sec4', 'sec5']);
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const MAX_CHIFFRE = 4096;                                       // octets d'un champ chiffré

export default {
  async fetch(requete, env, ctx) {
    const url = new URL(requete.url);
    let sql;
    try {
      verifierOrigine(requete, env, url);
      if (url.pathname === '/api/sante') {
        sql = connexion(env);
        await sql`select 1`;
        return json({ ok: true });
      }
      const qui = await verifierJeton(requete, env);
      if (env.LIMITE) {
        const { success } = await env.LIMITE.limit({ key: qui.authId });
        if (!success) throw new ErreurHttp(429, 'trop de requêtes, réessayez dans une minute');
      }
      sql = connexion(env);
      const enseignant = await ouvrirSession(sql, qui.authId, qui.courriel);
      const ctxReq = { requete, env, url, sql, enseignant, ip: await empreinteIp(requete, env) };
      return await router(ctxReq);
    } catch (e) {
      if (e instanceof ErreurHttp) return json({ erreur: e.message }, e.statut);
      console.error('erreur interne', e && e.code, e && e.message);   // jamais de contenu de requête dans les journaux
      return json({ erreur: 'erreur interne' }, 500);
    } finally {
      if (sql) ctx.waitUntil(sql.end({ timeout: 2 }));
    }
  },
};

async function router(c) {
  const { requete, url } = c;
  const m = requete.method;
  const p = url.pathname.replace(/\/$/, '');
  let r;
  if (p === '/api/session' && m === 'POST') return session(c);
  if (p === '/api/moi' && m === 'GET') return moi(c);
  if (p === '/api/moi' && m === 'PATCH') return modifierMoi(c);
  if (p === '/api/coffre' && m === 'GET') return lireCoffre(c);
  if (p === '/api/coffre' && m === 'PUT') return ecrireCoffre(c);
  if (p === '/api/groupes' && m === 'GET') return groupes(c);
  if (p === '/api/groupes' && m === 'POST') return creerGroupe(c);
  if ((r = p.match(/^\/api\/groupes\/([^/]+)\/eleves$/))) {
    if (!UUID.test(r[1])) throw new ErreurHttp(404, 'groupe introuvable');
    if (m === 'GET') return eleves(c, r[1]);
    if (m === 'POST') return ajouterEleves(c, r[1]);
  }
  if (p === '/api/journal' && m === 'GET') return journal(c);
  throw new ErreurHttp(404, 'route inconnue');
}

// ───────────── Routes ─────────────

async function session(c) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    await noter(tx, c, 'connexion');
    return json(await profil(tx, c.enseignant));
  });
}

async function moi(c) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => json(await profil(tx, c.enseignant)));
}

async function modifierMoi(c) {
  const d = await corps(c.requete);
  const champs = {};
  if (d.nom_affiche !== undefined) champs.nom_affiche = texte(d.nom_affiche, 80);
  if (d.langue !== undefined) { if (!['fr', 'en'].includes(d.langue)) throw new ErreurHttp(400, 'langue invalide'); champs.langue = d.langue; }
  if (d.cle_publique !== undefined) champs.cle_publique = clePublique(d.cle_publique);
  if (!Object.keys(champs).length) throw new ErreurHttp(400, 'rien à modifier');
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    if (champs.cle_publique) champs.cle_publique = tx.json(champs.cle_publique);
    await tx`update enseignants set ${tx(champs)} where id = ${c.enseignant}`;
    return json(await profil(tx, c.enseignant));
  });
}

async function lireCoffre(c) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    const [k] = await tx`select * from coffres where enseignant = ${c.enseignant}`;
    if (!k) throw new ErreurHttp(404, 'aucun coffre');
    return json({
      cle_par_phrase: versB64(k.cle_par_phrase), sel_phrase: versB64(k.sel_phrase), iterations_phrase: k.iterations_phrase,
      cle_par_recuperation: versB64(k.cle_par_recuperation), cle_par_passkey: versB64(k.cle_par_passkey), cle_privee_ecdh: versB64(k.cle_privee_ecdh),
      verificateur: versB64(k.verificateur), modifie_le: k.modifie_le,
    });
  });
}

// Le navigateur envoie la clé maîtresse déjà enveloppée : le serveur ne voit jamais la clé ni la phrase secrète.
async function ecrireCoffre(c) {
  const d = await corps(c.requete);
  const k = {
    enseignant: c.enseignant,
    cle_par_phrase: chiffre(d.cle_par_phrase, 'cle_par_phrase'),
    sel_phrase: chiffre(d.sel_phrase, 'sel_phrase'),
    iterations_phrase: Number.isInteger(d.iterations_phrase) && d.iterations_phrase >= 600000 ? d.iterations_phrase : null,
    cle_par_recuperation: chiffre(d.cle_par_recuperation, 'cle_par_recuperation'),
    cle_par_passkey: d.cle_par_passkey == null ? null : chiffre(d.cle_par_passkey, 'cle_par_passkey'),
    cle_privee_ecdh: d.cle_privee_ecdh == null ? null : chiffre(d.cle_privee_ecdh, 'cle_privee_ecdh'),
    verificateur: chiffre(d.verificateur, 'verificateur'),
  };
  if (!k.iterations_phrase) throw new ErreurHttp(400, 'au moins 600 000 itérations');
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    await tx`insert into coffres ${tx(k)} on conflict (enseignant) do update set
      cle_par_phrase = excluded.cle_par_phrase, sel_phrase = excluded.sel_phrase, iterations_phrase = excluded.iterations_phrase,
      cle_par_recuperation = excluded.cle_par_recuperation, cle_par_passkey = excluded.cle_par_passkey, cle_privee_ecdh = excluded.cle_privee_ecdh,
      verificateur = excluded.verificateur, modifie_le = now()`;
    await noter(tx, c, 'coffre.enregistrer');
    return json({ ok: true });
  });
}

async function groupes(c) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    const lignes = await tx`select g.id, g.nom_chiffre, g.niveau, g.annee_scolaire, g.programmes, m.role, m.cle_groupe_enveloppee,
        (select count(*) from eleves e where e.groupe = g.id and e.actif)::int as nb_eleves
      from groupes g join membres_groupe m on m.groupe = g.id and m.enseignant = ${c.enseignant}
      order by g.annee_scolaire desc, g.niveau`;
    return json(lignes.map((g) => ({ ...g, nom_chiffre: versB64(g.nom_chiffre), cle_groupe_enveloppee: versB64(g.cle_groupe_enveloppee) })));
  });
}

async function creerGroupe(c) {
  const d = await corps(c.requete);
  if (!NIVEAUX.has(d.niveau)) throw new ErreurHttp(400, 'niveau invalide');
  if (!/^20\d\d-20\d\d$/.test(d.annee_scolaire || '')) throw new ErreurHttp(400, 'année scolaire invalide (ex. 2026-2027)');
  const programmes = Array.isArray(d.programmes) ? d.programmes : [];
  if (programmes.length > 20 || !programmes.every((x) => typeof x === 'string' && /^(pri|sec)-[a-z0-9]{2,8}$/.test(x))) throw new ErreurHttp(400, 'programme invalide');
  const tableau = '{' + programmes.join(',') + '}';   // littéral de tableau Postgres (contenu validé ci-dessus)
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    if (programmes.length) {
      const [{ n }] = await tx`select count(*)::int as n from programmes where programme = any(${tableau}::text[])`;
      if (n !== programmes.length) throw new ErreurHttp(400, 'programme inconnu');
    }
    const [{ id }] = await tx`select creer_groupe(${chiffre(d.nom_chiffre, 'nom_chiffre')}, ${d.niveau}, ${d.annee_scolaire},
      ${tableau}::text[], ${chiffre(d.cle_groupe_enveloppee, 'cle_groupe_enveloppee')}) as id`;
    await noter(tx, c, 'groupe.creer', 'groupe:' + id);
    return json({ id }, 201);
  });
}

async function eleves(c, groupe) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    const lignes = await tx`select id, nom_chiffre, actif from eleves where groupe = ${groupe} order by id`;
    const [g] = await tx`select 1 from groupes where id = ${groupe}`;
    if (!g) throw new ErreurHttp(404, 'groupe introuvable');
    await noter(tx, c, 'eleves.lire', 'groupe:' + groupe);
    return json(lignes.map((e) => ({ ...e, nom_chiffre: versB64(e.nom_chiffre) })));
  });
}

// Importation d'une liste : les noms arrivent déjà chiffrés par le navigateur ; les codes sont tirés au hasard ici.
async function ajouterEleves(c, groupe) {
  const d = await corps(c.requete);
  if (!Array.isArray(d.eleves) || !d.eleves.length || d.eleves.length > 60) throw new ErreurHttp(400, 'entre 1 et 60 élèves');
  const lignes = d.eleves.map((e) => ({ id: codeEleve(), groupe, nom_chiffre: chiffre(e.nom_chiffre, 'nom_chiffre') }));
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    try {
      await tx`insert into eleves ${tx(lignes)}`;
    } catch (e) {
      if (e.code === '42501') throw new ErreurHttp(404, 'groupe introuvable');   // refusé par la RLS
      throw e;
    }
    await noter(tx, c, 'eleves.ajouter', 'groupe:' + groupe);
    return json(lignes.map((l) => ({ id: l.id })), 201);
  });
}

async function journal(c) {
  return commeEnseignante(c.sql, c.enseignant, async (tx) => {
    const lignes = await tx`select j.action, j.objet, j.quand, (j.enseignant = ${c.enseignant}) as par_moi, e.nom_affiche as par
      from journal_acces j left join enseignants e on e.id = j.enseignant order by j.quand desc limit 200`;
    return json(lignes);
  });
}

// ───────────── Outils ─────────────

async function profil(tx, id) {
  const [e] = await tx`select id, courriel, nom_affiche, langue, centre_services, cle_publique,
    exists (select 1 from coffres where enseignant = ${id}) as a_un_coffre from enseignants where id = ${id}`;
  return e;
}

async function noter(tx, c, action, objet = null) {
  await tx`insert into journal_acces (enseignant, action, objet, empreinte_ip) values (${c.enseignant}, ${action}, ${objet}, ${c.ip})`;
}

// L'adresse IP n'est jamais conservée : seulement une empreinte salée (HMAC), utile pour repérer un accès inhabituel.
async function empreinteIp(requete, env) {
  const ip = requete.headers.get('CF-Connecting-IP');
  if (!ip || !env.SEL_IP) return null;
  const cle = await crypto.subtle.importKey('raw', new TextEncoder().encode(env.SEL_IP), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', cle, new TextEncoder().encode(ip));
  return Buffer.from(sig).subarray(0, 12).toString('base64url');
}

// Refuse les requêtes qui modifient des données depuis un autre site (protection CSRF en plus du jeton).
function verifierOrigine(requete, env, url) {
  if (requete.method === 'GET' || requete.method === 'HEAD') return;
  const origine = requete.headers.get('Origin');
  if (origine && origine !== url.origin && origine !== env.ORIGINE) throw new ErreurHttp(403, 'origine refusée');
}

async function corps(requete) {
  if (!(requete.headers.get('Content-Type') || '').startsWith('application/json')) throw new ErreurHttp(415, 'JSON attendu');
  const brut = await requete.text();
  if (brut.length > 64 * 1024) throw new ErreurHttp(413, 'requête trop grande');
  try { return JSON.parse(brut); } catch { throw new ErreurHttp(400, 'JSON invalide'); }
}

function texte(x, max) {
  if (typeof x !== 'string' || x.length > max) throw new ErreurHttp(400, `texte invalide (${max} caractères au plus)`);
  return x.trim();
}

function chiffre(b64, nom) {
  if (typeof b64 !== 'string' || !/^[A-Za-z0-9+/]+={0,2}$/.test(b64)) throw new ErreurHttp(400, `${nom} : base64 attendu`);
  const o = versOctets(b64);
  if (!o.length || o.length > MAX_CHIFFRE) throw new ErreurHttp(400, `${nom} : taille invalide`);
  return o;
}

function clePublique(jwk) {
  if (!jwk || jwk.kty !== 'EC' || jwk.crv !== 'P-256' || typeof jwk.x !== 'string' || typeof jwk.y !== 'string' || jwk.d)
    throw new ErreurHttp(400, 'clé publique ECDH P-256 attendue (sans partie privée)');
  return { kty: 'EC', crv: 'P-256', x: jwk.x, y: jwk.y };
}

function codeEleve() {
  const A = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ';   // sans I ni O, pour éviter les confusions
  const o = crypto.getRandomValues(new Uint8Array(6));
  const c = [...o].map((b) => A[b % A.length]).join('');
  return c.slice(0, 4) + '-' + c.slice(4);
}
