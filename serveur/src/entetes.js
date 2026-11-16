// En-têtes de sécurité des réponses de l'API (spécification, section 8).
export const ENTETES_SECURITE = {
  'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'",
  'Cross-Origin-Resource-Policy': 'same-origin',
  'Cache-Control': 'no-store',
};

export function json(donnees, statut = 200, extra = {}) {
  return new Response(JSON.stringify(donnees), {
    status: statut,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...ENTETES_SECURITE, ...extra },
  });
}

export class ErreurHttp extends Error {
  constructor(statut, message) { super(message); this.statut = statut; }
}
