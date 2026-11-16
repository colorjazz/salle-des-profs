-- Test du cloisonnement (RLS) avec le rôle de l'application. Chaque vérification lève une erreur si elle échoue.
-- Usage (base de test seulement) : psql "$URL_TEST" -v ON_ERROR_STOP=1 -f tests/cloisonnement.sql
\set QUIET on
\o /dev/null
set search_path = sdp, public;
create temp table ids (nom text primary key, id uuid);
grant select, insert on ids to sdp_app;  -- table temporaire : visible seulement dans cette session
set role sdp_app;

create or replace function pg_temp.verifier(cond boolean, msg text) returns void language plpgsql as $$
begin if not cond then raise exception 'ÉCHEC : %', msg; end if; raise notice 'ok : %', msg; end $$;

-- Sans enseignante fixée, rien n'est visible, mais le référentiel l'est.
select pg_temp.verifier((select count(*) from enseignants) = 0, 'aucune enseignante visible sans session');
select pg_temp.verifier((select count(*) from savoirs) > 10000, 'référentiel lisible');

reset role;
insert into ids select 'A', ouvrir_session('00000000-0000-0000-0000-00000000000a', 'a@ecole.qc.ca');
insert into ids select 'B', ouvrir_session('00000000-0000-0000-0000-00000000000b', 'b@ecole.qc.ca');
insert into ids select 'C', ouvrir_session('00000000-0000-0000-0000-00000000000c', 'direction@ecole.qc.ca');
set role sdp_app;

-- A crée un groupe et un élève
begin;
select set_config('sdp.enseignant', (select id::text from ids where nom='A'), true);
insert into ids select 'G', creer_groupe('\x01'::bytea, '4', '2026-2027', array['pri-fra'], '\x02'::bytea);
insert into eleves values ('7F3A-K2', (select id from ids where nom='G'), '\x03'::bytea);
insert into evaluations (groupe, titre) values ((select id from ids where nom='G'), 'Dictée 1');
insert into membres_groupe (groupe, enseignant, role) values ((select id from ids where nom='G'), (select id from ids where nom='C'), 'direction');
select pg_temp.verifier((select count(*) from eleves) = 1, 'A voit son élève');
select pg_temp.verifier((select count(*) from enseignants) = 2, 'A voit son profil et la direction de son groupe');
commit;

-- B ne voit rien et ne peut rien écrire dans le groupe de A
begin;
select set_config('sdp.enseignant', (select id::text from ids where nom='B'), true);
select pg_temp.verifier((select count(*) from groupes) = 0, 'B ne voit pas le groupe de A');
select pg_temp.verifier((select count(*) from eleves) = 0, 'B ne voit pas les élèves de A');
select pg_temp.verifier((select count(*) from enseignants) = 1, 'B ne voit que son profil');
select pg_temp.verifier((select count(*) from evaluations) = 0, 'B ne voit pas les évaluations de A');
commit;
do $$ begin
  perform set_config('sdp.enseignant', (select id::text from ids where nom='B'), true);
  insert into eleves values ('XXXX-B1', (select id from ids where nom='G'), '\x00'::bytea);
  raise exception 'ÉCHEC : B a pu ajouter un élève au groupe de A';
exception when insufficient_privilege then raise notice 'ok : B ne peut pas écrire dans le groupe de A';
end $$;
do $$ begin
  perform set_config('sdp.enseignant', (select id::text from ids where nom='B'), true);
  insert into membres_groupe values ((select id from ids where nom='G'), (select id from ids where nom='B'), 'titulaire', null);
  raise exception 'ÉCHEC : B a pu s''ajouter au groupe de A';
exception when insufficient_privilege then raise notice 'ok : B ne peut pas s''ajouter au groupe de A';
end $$;

-- La direction voit le groupe, crée une trousse, mais ne voit ni élèves ni évaluations
begin;
select set_config('sdp.enseignant', (select id::text from ids where nom='C'), true);
select pg_temp.verifier((select count(*) from groupes) = 1, 'la direction voit le groupe');
select pg_temp.verifier((select count(*) from eleves) = 0, 'la direction ne voit pas les élèves');
select pg_temp.verifier((select count(*) from evaluations) = 0, 'la direction ne voit pas les évaluations');
insert into trousses_suppleance (groupe, jour, creee_par, role_createur, contenu)
  values ((select id from ids where nom='G'), current_date, (select id from ids where nom='C'), 'direction', '{}');
insert into journal_acces (enseignant, action, objet) values ((select id from ids where nom='C'), 'trousse.generer', 'groupe:' || (select id from ids where nom='G'));
select pg_temp.verifier((select count(*) from trousses_suppleance) = 1, 'la direction crée une trousse');
commit;
do $$ begin
  perform set_config('sdp.enseignant', (select id::text from ids where nom='C'), true);
  update groupes set niveau = '5';
  if found then raise exception 'ÉCHEC : la direction a modifié le groupe'; end if;
  raise notice 'ok : la direction ne modifie pas le groupe';
end $$;

-- A voit, dans son journal, que la direction a généré une trousse
begin;
select set_config('sdp.enseignant', (select id::text from ids where nom='A'), true);
select pg_temp.verifier((select count(*) from journal_acces where action = 'trousse.generer') = 1, 'A est avisée de la trousse générée par la direction');
select pg_temp.verifier((select count(*) from trousses_suppleance) = 1, 'A voit la trousse');
commit;

do $$ begin
  perform set_config('sdp.enseignant', (select id::text from ids where nom='A'), true);
  update enseignants set auth_id = gen_random_uuid() where id = (select id from ids where nom='A');
  raise exception 'ÉCHEC : A a pu changer son identifiant de connexion';
exception when insufficient_privilege then raise notice 'ok : identifiant de connexion non modifiable';
end $$;

-- Le registre des incidents est inaccessible à l'application
do $$ begin
  perform count(*) from incidents;
  raise exception 'ÉCHEC : l''application lit le registre des incidents';
exception when insufficient_privilege then raise notice 'ok : registre des incidents inaccessible';
end $$;

reset role;
delete from enseignants where auth_id::text like '00000000-0000-0000-0000-00000000000%';
delete from groupes where id = (select id from ids where nom='G');
\o
\echo 'Tous les tests de cloisonnement réussissent.'
