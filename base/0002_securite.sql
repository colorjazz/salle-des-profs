-- Migration 0002 : rôle de l'application et sécurité au niveau des lignes (RLS).
-- Seconde barrière : même si le Worker oubliait un filtre, Postgres ne rend que les lignes de l'enseignante connectée.
-- Le Worker ouvre une transaction par requête et y fixe l'enseignante :
--   select set_config('sdp.enseignant', '<uuid>', true);
-- Sans cette valeur, aucune donnée d'enseignante n'est visible.

begin;
set local search_path = sdp, public;

-- Le rôle de l'application : pas propriétaire des tables, donc soumis à la RLS.
do $$ begin
  if not exists (select from pg_roles where rolname = 'sdp_app') then
    create role sdp_app login nobypassrls;   -- mot de passe fixé à part, jamais dans le dépôt
  end if;
end $$;

grant usage on schema sdp to sdp_app;
grant select on programmes, savoirs, modules, savoirs_modules to sdp_app;
grant select, insert, update, delete on enseignants, coffres, groupes, membres_groupe, eleves, evaluations,
  questions, copies, resultats_question, fautes_langue, commentaires, trousses_suppleance to sdp_app;
grant select, insert on journal_acces to sdp_app;
-- Une enseignante ne modifie que ces colonnes de son profil (jamais auth_id ni courriel, gérés par la connexion).
revoke update on enseignants from sdp_app;
grant update (nom_affiche, langue, centre_services, cle_publique) on enseignants to sdp_app;
revoke insert on enseignants from sdp_app;  -- création par ouvrir_session()
grant usage on all sequences in schema sdp to sdp_app;
-- incidents : aucun accès pour l'application.

-- ───────────── Fonctions d'appui ─────────────

create or replace function moi() returns uuid language sql stable as $$
  select nullif(current_setting('sdp.enseignant', true), '')::uuid
$$;

-- Groupes de l'enseignante connectée. SECURITY DEFINER : évite la récursion des politiques sur membres_groupe.
-- avec_eleves = false inclut la direction, qui voit les groupes mais jamais les élèves ni les résultats.
create or replace function mes_groupes(avec_eleves boolean default true) returns setof uuid
language sql stable security definer set search_path = sdp, public as $$
  select groupe from membres_groupe
  where enseignant = moi() and (not avec_eleves or role <> 'direction')
$$;

create or replace function mes_groupes_titulaire() returns setof uuid
language sql stable security definer set search_path = sdp, public as $$
  select groupe from membres_groupe where enseignant = moi() and role = 'titulaire'
$$;

-- Première connexion ou retour : crée ou retrouve l'enseignante à partir du jeton de Supabase Auth.
create or replace function ouvrir_session(p_auth uuid, p_courriel text) returns uuid
language plpgsql security definer set search_path = sdp, public as $$
declare v uuid;
begin
  insert into enseignants (auth_id, courriel) values (p_auth, lower(p_courriel))
  on conflict (auth_id) do update set vu_le = now(), courriel = excluded.courriel
  returning id into v;
  return v;
end $$;

-- Crée un groupe et en fait l'enseignante connectée la titulaire, en une seule opération.
create or replace function creer_groupe(p_nom bytea, p_niveau text, p_annee text, p_programmes text[], p_cle bytea)
returns uuid language plpgsql security definer set search_path = sdp, public as $$
declare g uuid;
begin
  if moi() is null then raise exception 'aucune enseignante connectée'; end if;
  insert into groupes (nom_chiffre, niveau, annee_scolaire, programmes) values (p_nom, p_niveau, p_annee, p_programmes) returning id into g;
  insert into membres_groupe (groupe, enseignant, role, cle_groupe_enveloppee) values (g, moi(), 'titulaire', p_cle);
  return g;
end $$;

revoke all on function mes_groupes(boolean), mes_groupes_titulaire(), ouvrir_session(uuid, text), creer_groupe(bytea, text, text, text[], bytea) from public;
grant execute on function moi(), mes_groupes(boolean), mes_groupes_titulaire(), ouvrir_session(uuid, text), creer_groupe(bytea, text, text, text[], bytea) to sdp_app;

-- ───────────── Politiques ─────────────

alter table enseignants enable row level security;
create policy soi on enseignants using (id = moi()) with check (id = moi());
-- Voir le nom et la clé publique des collègues d'un même groupe (partage).
create policy collegues on enseignants for select using (id in (select enseignant from membres_groupe where groupe in (select mes_groupes(false))));

alter table coffres enable row level security;
create policy soi on coffres using (enseignant = moi()) with check (enseignant = moi());

alter table groupes enable row level security;
create policy membre on groupes for select using (id in (select mes_groupes(false)));
create policy titulaire on groupes for update using (id in (select mes_groupes_titulaire()));
create policy titulaire_supprime on groupes for delete using (id in (select mes_groupes_titulaire()));
-- La création passe par creer_groupe().

alter table membres_groupe enable row level security;
create policy membre on membres_groupe for select using (groupe in (select mes_groupes(false)));
create policy titulaire on membres_groupe for all
  using (groupe in (select mes_groupes_titulaire()))
  with check (groupe in (select mes_groupes_titulaire()));
create policy quitter on membres_groupe for delete using (enseignant = moi());

alter table eleves enable row level security;
create policy groupe on eleves using (groupe in (select mes_groupes())) with check (groupe in (select mes_groupes()));

alter table evaluations enable row level security;
create policy groupe on evaluations using (groupe in (select mes_groupes())) with check (groupe in (select mes_groupes()));

alter table questions enable row level security;
create policy groupe on questions using (evaluation in (select id from evaluations)) with check (evaluation in (select id from evaluations));

alter table copies enable row level security;
create policy groupe on copies using (evaluation in (select id from evaluations)) with check (evaluation in (select id from evaluations));

alter table resultats_question enable row level security;
create policy groupe on resultats_question using (copie in (select id from copies)) with check (copie in (select id from copies));

alter table fautes_langue enable row level security;
create policy groupe on fautes_langue using (copie in (select id from copies)) with check (copie in (select id from copies));

alter table commentaires enable row level security;
create policy groupe on commentaires using (copie in (select id from copies)) with check (copie in (select id from copies));

-- La direction voit et crée les trousses de suppléance de ses groupes, sans accès aux élèves.
alter table trousses_suppleance enable row level security;
create policy groupe on trousses_suppleance using (groupe in (select mes_groupes(false))) with check (groupe in (select mes_groupes(false)));

alter table journal_acces enable row level security;
create policy soi on journal_acces using (enseignant = moi()) with check (enseignant = moi());
-- L'enseignante voit aussi ce que d'autres ont fait sur ses groupes (ex. la direction qui génère une trousse).
create policy mes_groupes on journal_acces for select using (objet in (select 'groupe:' || g from mes_groupes() g));

commit;
