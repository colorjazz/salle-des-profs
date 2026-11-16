// Essai de bout en bout du Worker en local : wrangler dev + Postgres local + faux émetteur de jetons (JWKS).
// Préalable : base de test avec base/0001, 0002 et le référentiel chargés.
// Usage : PG_LOCAL="postgres://sdp_app@127.0.0.1:5499/postgres" node tests/essai.mjs
import http from 'node:http';
import { spawn } from 'node:child_process';
import { generateKeyPair, exportJWK, SignJWT } from 'jose';

const PORT_JWKS = 8899, PORT_API = 8788;
const EMETTEUR = `http://127.0.0.1:${PORT_JWKS}`;
const { publicKey, privateKey } = await generateKeyPair('ES256');
const jwk = { ...(await exportJWK(publicKey)), kid: 'essai', alg: 'ES256', use: 'sig' };
const jwks = http.createServer((q, r) => { r.setHeader('Content-Type', 'application/json'); r.end(JSON.stringify({ keys: [jwk] })); }).listen(PORT_JWKS);

const jeton = (sub, email, o = {}) => new SignJWT({ email, role: 'authenticated' }).setProtectedHeader({ alg: 'ES256', kid: 'essai' })
  .setSubject(sub).setIssuer(o.iss || EMETTEUR + '/auth/v1').setAudience('authenticated').setIssuedAt().setExpirationTime(o.exp || '1h').sign(privateKey);

const dev = spawn('npx', ['wrangler', 'dev', '--port', String(PORT_API), '--var', `SUPABASE_URL:${EMETTEUR}`, '--var', 'SEL_IP:essai'], {
  env: { ...process.env, CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_BASE: process.env.PG_LOCAL, NO_PROXY: '127.0.0.1,localhost', no_proxy: '127.0.0.1,localhost' },
  stdio: ['ignore', 'pipe', 'pipe'], detached: true,
});
let journalDev = '';
dev.stdout.on('data', (d) => (journalDev += d)); dev.stderr.on('data', (d) => (journalDev += d));
const API = `http://127.0.0.1:${PORT_API}`;
try { await fetch(API + '/api/sante'); console.error('Un serveur occupe déjà le port ' + PORT_API + ' : arrêtez-le avant l’essai.'); process.exit(2); } catch {}
for (let i = 0; i < 60; i++) { try { await fetch(API + '/api/sante'); break; } catch { await new Promise((r) => setTimeout(r, 1000)); } }

let echecs = 0;
const verifier = (cond, msg) => { console.log((cond ? 'ok    ' : 'ÉCHEC ') + msg); if (!cond) echecs++; };
const appel = async (chemin, o = {}) => {
  const r = await fetch(API + chemin, { method: o.methode || 'GET', headers: { ...(o.jeton ? { Authorization: 'Bearer ' + o.jeton } : {}), ...(o.corps ? { 'Content-Type': 'application/json' } : {}), ...(o.entetes || {}) }, body: o.corps ? JSON.stringify(o.corps) : undefined });
  let d = null; try { d = await r.json(); } catch {}
  return { s: r.status, d, h: r.headers };
};
const b64 = (n) => Buffer.from(crypto.getRandomValues(new Uint8Array(n))).toString('base64');

try {
  const A = await jeton(crypto.randomUUID(), 'a@ecole.qc.ca'), B = await jeton(crypto.randomUUID(), 'b@ecole.qc.ca');
  let r = await appel('/api/sante');
  verifier(r.s === 200 && r.d.ok, 'santé : la base répond');
  verifier(r.h.get('strict-transport-security') && r.h.get('content-security-policy'), 'en-têtes de sécurité présents');
  verifier((await appel('/api/moi')).s === 401, 'sans jeton : 401');
  verifier((await appel('/api/moi', { jeton: await jeton(crypto.randomUUID(), 'x@y.ca', { iss: 'https://pirate.example/auth/v1' }) })).s === 401, 'émetteur étranger : 401');
  verifier((await appel('/api/moi', { jeton: A.slice(0, -4) + 'AAAA' })).s === 401, 'signature falsifiée : 401');

  r = await appel('/api/session', { methode: 'POST', jeton: A });
  verifier(r.s === 200 && r.d.courriel === 'a@ecole.qc.ca' && r.d.a_un_coffre === false, 'première connexion : compte créé, sans coffre');
  r = await appel('/api/moi', { methode: 'PATCH', jeton: A, corps: { nom_affiche: 'Mme Tremblay', langue: 'fr' } });
  verifier(r.s === 200 && r.d.nom_affiche === 'Mme Tremblay', 'profil modifié');
  verifier((await appel('/api/moi', { methode: 'PATCH', jeton: A, corps: { nom_affiche: 'x' }, entetes: { Origin: 'https://pirate.example' } })).s === 403, 'autre origine : refusée');

  verifier((await appel('/api/coffre', { methode: 'PUT', jeton: A, corps: { cle_par_phrase: b64(60), sel_phrase: b64(16), iterations_phrase: 1000, cle_par_recuperation: b64(60), verificateur: b64(40) } })).s === 400, 'coffre : moins de 600 000 itérations refusé');
  const coffre = { cle_par_phrase: b64(60), sel_phrase: b64(16), iterations_phrase: 600000, cle_par_recuperation: b64(60), verificateur: b64(40) };
  verifier((await appel('/api/coffre', { methode: 'PUT', jeton: A, corps: coffre })).s === 200, 'coffre enregistré');
  r = await appel('/api/coffre', { jeton: A });
  verifier(r.s === 200 && r.d.cle_par_phrase === coffre.cle_par_phrase, 'coffre relu à l’identique');
  verifier((await appel('/api/coffre', { jeton: B })).s === 404, 'B n’a pas accès au coffre de A');

  verifier((await appel('/api/groupes', { methode: 'POST', jeton: A, corps: { nom_chiffre: b64(30), cle_groupe_enveloppee: b64(60), niveau: 'sec9', annee_scolaire: '2026-2027' } })).s === 400, 'niveau invalide refusé');
  r = await appel('/api/groupes', { methode: 'POST', jeton: A, corps: { nom_chiffre: b64(30), cle_groupe_enveloppee: b64(60), niveau: '4', annee_scolaire: '2026-2027', programmes: ['pri-fra', 'pri-mat'] } });
  verifier(r.s === 201 && r.d.id, 'groupe créé'); if (r.s !== 201) console.log(r.s, r.d);
  const G = r.d.id;
  r = await appel(`/api/groupes/${G}/eleves`, { methode: 'POST', jeton: A, corps: { eleves: [{ nom_chiffre: b64(40) }, { nom_chiffre: b64(40) }, { nom_chiffre: b64(40) }] } });
  verifier(r.s === 201 && r.d.length === 3 && /^[0-9A-Z]{4}-[0-9A-Z]{2}$/.test(r.d[0].id), 'trois élèves ajoutés avec des codes pseudonymes');
  r = await appel('/api/groupes', { jeton: A });
  verifier(r.s === 200 && r.d.length === 1 && r.d[0].nb_eleves === 3 && r.d[0].role === 'titulaire', 'A voit son groupe (3 élèves, titulaire)');

  await appel('/api/session', { methode: 'POST', jeton: B });
  verifier((await appel('/api/groupes', { jeton: B })).d.length === 0, 'B ne voit aucun groupe');
  verifier((await appel(`/api/groupes/${G}/eleves`, { jeton: B })).s === 404, 'B ne lit pas les élèves de A');
  verifier((await appel(`/api/groupes/${G}/eleves`, { methode: 'POST', jeton: B, corps: { eleves: [{ nom_chiffre: b64(40) }] } })).s === 404, 'B n’ajoute pas d’élève chez A');

  r = await appel('/api/journal', { jeton: A });
  const actions = r.d.map((x) => x.action);
  verifier(['connexion', 'coffre.enregistrer', 'groupe.creer', 'eleves.ajouter'].every((a) => actions.includes(a)), 'journal d’accès tenu');
  verifier(r.d.every((x) => !('empreinte_ip' in x)), 'le journal ne renvoie pas l’empreinte IP');
  verifier((await appel('/api/journal', { jeton: B })).d.every((x) => x.action === 'connexion'), 'B ne voit pas le journal de A');
  verifier((await appel('/api/inconnue', { jeton: A })).s === 404, 'route inconnue : 404');
  verifier((await appel('/liste.html')).s === 200, 'les pages du site sont servies');
} catch (e) {
  echecs++; console.error(e); console.error(journalDev.slice(-3000));
} finally {
  try { process.kill(-dev.pid, 'SIGTERM'); } catch {}  jwks.close();
  console.log(echecs ? `${echecs} échec(s)` : 'Tous les essais réussissent.');
  if (echecs && process.env.VERBEUX) console.log(journalDev.slice(-4000));
  process.exit(echecs ? 1 : 0);
}
