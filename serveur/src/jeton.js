// Vérifie le jeton de session émis par Supabase Auth (clés asymétriques publiées en JWKS).
import { createRemoteJWKSet, jwtVerify } from 'jose';
import { ErreurHttp } from './entetes.js';

const jeux = new Map();

export async function verifierJeton(requete, env) {
  const entete = requete.headers.get('Authorization') || '';
  const m = entete.match(/^Bearer\s+(\S+)$/);
  if (!m) throw new ErreurHttp(401, 'connexion requise');
  const base = env.SUPABASE_URL.replace(/\/$/, '');
  if (!jeux.has(base)) jeux.set(base, createRemoteJWKSet(new URL(base + '/auth/v1/.well-known/jwks.json')));
  try {
    const { payload } = await jwtVerify(m[1], jeux.get(base), {
      issuer: base + '/auth/v1',
      audience: 'authenticated',
      algorithms: ['ES256', 'RS256'],
    });
    if (!payload.sub || !payload.email) throw new Error('jeton incomplet');
    return { authId: payload.sub, courriel: payload.email };
  } catch (e) {
    console.warn('jeton refusé', e && e.code);   // jamais le jeton lui-même
    throw new ErreurHttp(401, 'session expirée ou invalide');
  }
}
