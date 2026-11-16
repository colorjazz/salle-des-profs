-- Salle des profs · base Postgres à Montréal (Supabase, ca-central-1)
-- Migration 0001 : tables du référentiel et des données des enseignantes.
-- Principes (spécification, sections 1 et 4) :
--   - aucune image de copie, aucun nom d'élève en clair : seulement des codes et des textes chiffrés (bytea) ;
--   - chaque table de données porte de quoi filtrer par enseignante ou par groupe (sécurité au niveau des lignes, 0002).
-- À exécuter par le rôle propriétaire (sdp_proprio), jamais par le rôle de l'application.

begin;

create schema if not exists sdp;
set local search_path = sdp, public;

-- ───────────── Référentiel (public, sans renseignement personnel) ─────────────
-- Chargé par outils/charger_referentiel.py à partir de maquettes/catalogue/.

create table programmes (
  programme   text primary key,            -- ex. 'sec-mat' (nom du fichier du catalogue)
  code        text not null,               -- ex. 'MAT'
  nom         text not null,
  ordre       text not null check (ordre in ('primaire', 'secondaire')),
  niveaux     text[] not null,
  version     text not null                -- empreinte de la source chargée
);

create table savoirs (
  programme   text not null references programmes on delete cascade,
  id          text not null,               -- ex. 'MAT-GEO-001' (le même code existe au primaire et au secondaire)
  section     text not null default '',    -- g : grande section de la PDA
  chemin      text not null default '',    -- s : titres au-dessus du savoir
  texte       text not null,               -- t : texte officiel
  progression jsonb not null default '{}', -- p : { "3": "A", "4": "M" } ou { "4": { "CST": "A" } }
  primary key (programme, id)
);

create table modules (
  programme   text not null references programmes on delete cascade,
  id          text not null,
  rang        int  not null,
  titre       text not null,
  description text not null default '',
  primary key (programme, id)
);

create table savoirs_modules (
  programme   text not null,
  savoir      text not null,
  module      text not null,
  libelle     text,                        -- libellé en langage clair (Gemini, validé)
  primary key (programme, savoir),
  foreign key (programme, savoir) references savoirs on delete cascade,
  foreign key (programme, module) references modules on delete cascade
);

-- ───────────── Données des enseignantes ─────────────

create table enseignants (
  id              uuid primary key default gen_random_uuid(),
  auth_id         uuid not null unique,     -- identifiant de Supabase Auth (sub du jeton)
  courriel        text not null,
  nom_affiche     text not null default '',
  langue          text not null default 'fr' check (langue in ('fr', 'en')),
  centre_services text,
  cle_publique    jsonb,                    -- ECDH P-256 au format JWK, pour le partage d'un groupe
  cree_le         timestamptz not null default now(),
  vu_le           timestamptz not null default now()
);

-- Clé maîtresse enveloppée de trois façons ; le serveur ne peut lire aucune d'elles.
create table coffres (
  enseignant                   uuid primary key references enseignants on delete cascade,
  cle_par_phrase               bytea not null,
  sel_phrase                   bytea not null,
  iterations_phrase            int   not null default 600000,
  cle_par_recuperation         bytea not null,
  cle_par_passkey              bytea,
  cle_privee_ecdh              bytea,         -- clé privée d'échange (partage de groupe), enveloppée par la clé maîtresse
  verificateur                 bytea not null, -- petit texte connu chiffré : confirme qu'une clé déverrouillée est la bonne
  modifie_le                   timestamptz not null default now()
);

create table groupes (
  id              uuid primary key default gen_random_uuid(),
  nom_chiffre     bytea not null,            -- ex. « 401 · Français » chiffré avec la clé du groupe
  niveau          text not null,             -- '1' à '6' (primaire) ou 'sec1' à 'sec5'
  annee_scolaire  text not null,             -- '2026-2027'
  programmes      text[] not null default '{}',
  cree_le         timestamptz not null default now()
);

create table membres_groupe (
  groupe          uuid not null references groupes on delete cascade,
  enseignant      uuid not null references enseignants on delete cascade,
  role            text not null check (role in ('titulaire', 'coenseignante', 'orthopedagogue', 'suppleante', 'direction')),
  cle_groupe_enveloppee bytea,               -- null pour la direction : elle ne déchiffre pas les noms
  ajoute_le       timestamptz not null default now(),
  primary key (groupe, enseignant)
);

create table eleves (
  id          text primary key,              -- code aléatoire, ex. '7F3A-K2'
  groupe      uuid not null references groupes on delete cascade,
  nom_chiffre bytea not null,
  actif       boolean not null default true
);
create index on eleves (groupe);

create table evaluations (
  id            uuid primary key default gen_random_uuid(),
  groupe        uuid not null references groupes on delete cascade,
  titre         text not null,
  programme     text,                      -- pas de clé étrangère : recharger le référentiel ne doit jamais toucher aux évaluations
  competences   text[] not null default '{}',
  etape         int check (etape between 1 and 3),
  date_prevue   date,
  bareme_total  numeric(6,2),
  grille        jsonb,
  corrige_texte text,
  cree_par      uuid references enseignants on delete set null,
  cree_le       timestamptz not null default now()
);
create index on evaluations (groupe);

create table questions (
  id          uuid primary key default gen_random_uuid(),
  evaluation  uuid not null references evaluations on delete cascade,
  numero      text not null,
  points_max  numeric(6,2) not null,
  critere     text,
  savoirs     text[] not null default '{}',
  unique (evaluation, numero)
);

create table copies (
  id          uuid primary key default gen_random_uuid(),
  evaluation  uuid not null references evaluations on delete cascade,
  eleve       text not null references eleves on delete cascade,
  statut      text not null default 'imprimee' check (statut in ('imprimee', 'numerisee', 'corrigee', 'validee')),
  lisibilite  text,
  nb_pages    int,
  manipulation boolean not null default false,
  unique (evaluation, eleve)
);

create table resultats_question (
  copie          uuid not null references copies on delete cascade,
  question       uuid not null references questions on delete cascade,
  points_ia      numeric(6,2),
  points_valides numeric(6,2),
  niveau         text,
  justification  text,
  valide_par     uuid references enseignants on delete set null,
  valide_le      timestamptz,
  primary key (copie, question)
);

create table fautes_langue (
  id        bigint generated always as identity primary key,
  copie     uuid not null references copies on delete cascade,
  categorie text not null,
  savoir    text,
  comptee   boolean not null default true
);

create table commentaires (
  copie        uuid primary key references copies on delete cascade,
  texte_ia     text,
  texte_valide text
);

create table trousses_suppleance (
  id               uuid primary key default gen_random_uuid(),
  groupe           uuid not null references groupes on delete cascade,
  jour             date not null,
  creee_par        uuid references enseignants on delete set null,
  role_createur    text not null check (role_createur in ('enseignante', 'direction')),
  contenu          jsonb not null,           -- aucun nom d'élève, aucun résultat
  partage_jusqu_au timestamptz,
  creee_le         timestamptz not null default now()
);

-- Exigé par la Loi 25. Aucune donnée d'élève dans « objet » : seulement des identifiants.
create table journal_acces (
  id          bigint generated always as identity primary key,
  enseignant  uuid references enseignants on delete set null,
  action      text not null,                 -- ex. 'connexion', 'groupe.creer', 'trousse.generer'
  objet       text,
  quand       timestamptz not null default now(),
  empreinte_ip text                          -- empreinte salée, jamais l'adresse en clair
);
create index on journal_acces (enseignant, quand desc);

-- Registre des incidents de confidentialité (Loi 25, art. 3.8). Rempli à la main par l'administration.
create table incidents (
  id            bigint generated always as identity primary key,
  constate_le   timestamptz not null,
  description   text not null,
  renseignements text not null,
  personnes     text,
  risque_serieux boolean,
  avis_cai_le   timestamptz,
  avis_personnes_le timestamptz,
  mesures       text,
  inscrit_le    timestamptz not null default now()
);

-- ───────────── Conservation (proposition de la spécification, à confirmer dans l'EFVP) ─────────────
create or replace function purger() returns table (quoi text, n bigint) language plpgsql as $$
begin
  delete from journal_acces where quand < now() - interval '2 years';
  get diagnostics n = row_count; quoi := 'journal_acces'; return next;
  -- Résultats : fin de l'année scolaire + 1 an. L'année '2024-2025' se termine le 30 juin 2025.
  delete from groupes where to_date(split_part(annee_scolaire, '-', 2) || '-06-30', 'YYYY-MM-DD') < now() - interval '1 year';
  get diagnostics n = row_count; quoi := 'groupes'; return next;
  delete from enseignants where vu_le < now() - interval '2 years';
  get diagnostics n = row_count; quoi := 'enseignants'; return next;
end $$;

commit;
