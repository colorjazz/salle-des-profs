# serveur

Le Worker Cloudflare de Salle des profs 2.0 : l'API (`/api/*`) et le service des pages.
Jalons J1 (socle) et J2 (coffre et groupes) de la spécification.

| Fichier | Rôle |
|---|---|
| `wrangler.toml` | Configuration : pages, Hyperdrive (Postgres à Montréal), limite de requêtes, variables |
| `src/index.js` | Routes de l'API |
| `src/jeton.js` | Vérification du jeton de Supabase Auth (clés publiques JWKS) |
| `src/base.js` | Connexion à Postgres ; chaque requête fixe l'enseignante pour la sécurité au niveau des lignes |
| `src/entetes.js` | En-têtes de sécurité, réponses JSON |
| `tests/essai.mjs` | Essai de bout en bout en local (24 vérifications) |

Le chiffrement des noms se fait dans le navigateur : `maquettes/js/coffre.js` (essais : `node --test tests/coffre.test.mjs` à la racine).
La base : `supabase/migrations/…_socle.sql`, `supabase/migrations/…_securite.sql`, essais `tests/cloisonnement.sql`.

## Routes

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/sante` | La base répond-elle ? (sans connexion) |
| POST | `/api/session` | Après la connexion : crée ou retrouve le compte, inscrit la connexion au journal |
| GET, PATCH | `/api/moi` | Profil (nom affiché, langue, clé publique de partage) |
| GET, PUT | `/api/coffre` | Clé maîtresse **enveloppée** (illisible pour le serveur) |
| GET, POST | `/api/groupes` | Groupes de l'enseignante ; création (nom chiffré) |
| GET, POST | `/api/groupes/:id/eleves` | Élèves (noms chiffrés, codes pseudonymes tirés par le serveur) |
| GET | `/api/journal` | Journal d'accès de l'enseignante et de ses groupes |

Toutes les routes sauf `/api/sante` exigent `Authorization: Bearer <jeton Supabase>`.

## Essai en local

Il faut Postgres 16 et Node 20+.

```bash
npm install
# base de test : appliquer les migrations (psql -1 -f supabase/migrations/…), charger le référentiel, donner un mot de passe à sdp_app
PG_LOCAL="postgres://sdp_app:motdepasse@127.0.0.1:5432/postgres" npm run essai
```

## Mise en ligne (quand les comptes existent)

1. **Supabase** : créer le projet en région **ca-central-1 (Montréal)**.
   - Authentication : activer le lien magique ; SMTP personnalisé = AWS SES à Montréal ; clés de signature **asymétriques** (JWT Signing Keys).
   - Les migrations de `supabase/migrations/` sont appliquées automatiquement par l'intégration GitHub de Supabase à chaque push sur `main`. Ensuite, dans l'éditeur SQL : `alter role sdp_app password '…'` (un long mot de passe aléatoire, gardé hors du dépôt).
   - Charger le référentiel : `python3 -I outils/charger_referentiel.py | psql "<URL du propriétaire>"`.
   - Vérifier le cloisonnement **sur une base de test** : `psql … -f tests/cloisonnement.sql`.
2. **Cloudflare** :
   - `npx wrangler hyperdrive create sdp-base --connection-string="postgres://sdp_app:…@<hôte du pooler>:6543/postgres" --caching-disabled`, puis copier l'identifiant dans `wrangler.toml`.
   - Mettre `SUPABASE_URL` et `ORIGINE` dans `wrangler.toml`.
   - `npx wrangler secret put SEL_IP` (une longue valeur aléatoire).
   - `npm run deployer`, puis relier le nom de domaine.
3. Vérifier : `https://<domaine>/api/sante` répond `{"ok":true}`.
