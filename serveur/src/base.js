// Accès à Postgres (Supabase, Montréal) par Hyperdrive.
// Chaque requête s'exécute dans une transaction où l'enseignante est fixée : la sécurité au niveau
// des lignes (supabase/migrations) ne rend alors que ses données, même si une requête oubliait un filtre.
import postgres from 'postgres';

export function connexion(env) {
  return postgres(env.BASE.connectionString, {
    max: 5, fetch_types: false, prepare: true,
    connection: { search_path: 'sdp,public', application_name: 'salle-des-profs' },
  });
}

export async function commeEnseignante(sql, enseignant, travail) {
  return sql.begin(async (tx) => {
    await tx`select set_config('sdp.enseignant', ${enseignant}, true)`;
    return travail(tx);
  });
}

export async function ouvrirSession(sql, authId, courriel) {
  const [{ id }] = await sql`select ouvrir_session(${authId}::uuid, ${courriel}) as id`;
  return id;
}

// Les champs chiffrés voyagent en base64 dans le JSON, et sont stockés en bytea.
export const versOctets = (b64) => (b64 == null ? null : Buffer.from(b64, 'base64'));
export const versB64 = (octets) => (octets == null ? null : Buffer.from(octets).toString('base64'));
