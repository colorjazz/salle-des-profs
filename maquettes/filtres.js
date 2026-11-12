/* Maquette : pastilles Groupe, Matière, Étape cliquables. Le choix est gardé d'une page à l'autre.
   Dans l'application, les groupes viendront de Microsoft 365 ou d'un import, et les matières, de la tâche de l'enseignante. */
(function () {
  var CLE = 'sdp-filtres';
  var GROUPES = [
    { nom: '4e année, groupe 41', detail: 'Titulaire · 24 élèves', ordre: 'primaire' },
    { nom: '4e année, groupe 42', detail: 'Enseignement partagé · mathématique', ordre: 'primaire' },
    { nom: '3e année, groupe 31', detail: 'Remplacement à long terme', ordre: 'primaire' },
    { titre: 'Autre profil (démonstration)' },
    { nom: '4e secondaire, groupe 402', detail: 'Histoire du Québec et du Canada · 31 élèves', ordre: 'secondaire' },
    { nom: '4e secondaire, groupe 404', detail: 'Histoire du Québec et du Canada · 29 élèves', ordre: 'secondaire' }
  ];
  var MATIERES = {
    primaire: ['Toutes les matières', 'Français', 'Mathématique', 'Science et technologie', 'Univers social', 'Culture et citoyenneté québécoise', 'Arts plastiques'],
    secondaire: ['Histoire du Québec et du Canada']
  };
  var ETAPES = ['Étape 1', 'Étape 2', 'Étape 3', 'Toute l’année'];
  var DEFAUT = { groupe: '4e année, groupe 41' };

  function lire() { try { return JSON.parse(localStorage.getItem(CLE)) || {}; } catch (e) { return {}; } }
  function ecrire(v) { try { localStorage.setItem(CLE, JSON.stringify(v)); } catch (e) {} }
  function ordreDe(nom) { var g = GROUPES.filter(function (x) { return x.nom === nom; })[0]; return g ? g.ordre : 'primaire'; }

  var css = document.createElement('style');
  css.textContent = '.filtre span{cursor:pointer;user-select:none;position:relative}' +
    '.filtre span:after{content:"";display:inline-block;width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);margin:0 0 3px 9px;opacity:.55}' +
    '.filtre span.ouvert{border-color:var(--encre,#33302b)}' +
    '.sdp-menu{position:absolute;z-index:50;min-width:250px;max-width:320px;background:#fffdf9;border:1px solid #ebe4d8;border-radius:12px;box-shadow:0 10px 30px rgba(51,48,43,.12);padding:6px;font-family:inherit;font-size:13px}' +
    '.sdp-menu div.o{padding:8px 10px;border-radius:8px;cursor:pointer;line-height:1.35}.sdp-menu div.o:hover{background:#f4f0e8}' +
    '.sdp-menu div.o.on{background:#efe9df;font-weight:500}.sdp-menu small{display:block;color:#8a8278;font-weight:400;font-size:12px}' +
    '.sdp-menu div.t{padding:10px 10px 4px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8a8278;border-top:1px solid #ebe4d8;margin-top:4px}' +
    '.sdp-avis{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:#33302b;color:#faf7f1;padding:10px 16px;border-radius:20px;font-size:13px;z-index:60;max-width:90vw;text-align:center;box-shadow:0 6px 20px rgba(0,0,0,.18)}';
  document.head.appendChild(css);

  function avis(texte) {
    var a = document.createElement('div'); a.className = 'sdp-avis'; a.textContent = texte; document.body.appendChild(a);
    setTimeout(function () { a.remove(); }, 3800);
  }
  function fermer() { var m = document.querySelector('.sdp-menu'); if (m) m.remove(); document.querySelectorAll('.filtre span.ouvert').forEach(function (s) { s.classList.remove('ouvert'); }); }

  function genre(span) {
    var t = span.textContent;
    if (/groupe/i.test(t)) return 'groupe';
    if (/^Étape|année$/i.test(t) || /Toute l’année/.test(t)) return 'etape';
    return 'matiere';
  }

  function appliquer() {
    var v = lire();
    document.querySelectorAll('.filtre span').forEach(function (s) {
      var g = genre(s);
      if (!s.dataset.defaut) s.dataset.defaut = s.textContent;
      if (v[g]) s.textContent = v[g];
      s.dataset.genre = g;
    });
  }

  function ouvrir(span) {
    fermer();
    var v = lire(), g = span.dataset.genre, groupe = v.groupe || DEFAUT.groupe;
    var m = document.createElement('div'); m.className = 'sdp-menu';
    var options = [];
    if (g === 'groupe') options = GROUPES;
    else if (g === 'matiere') options = MATIERES[ordreDe(groupe)].map(function (x) { return { nom: x }; });
    else options = ETAPES.map(function (x) { return { nom: x }; });
    options.forEach(function (o) {
      if (o.titre) { var t = document.createElement('div'); t.className = 't'; t.textContent = o.titre; m.appendChild(t); return; }
      var d = document.createElement('div'); d.className = 'o' + (span.textContent === o.nom ? ' on' : '');
      d.innerHTML = o.nom + (o.detail ? '<small>' + o.detail + '</small>' : '');
      d.onclick = function (e) {
        e.stopPropagation();
        var nv = lire(); nv[g] = o.nom;
        if (g === 'groupe') {   // la matière doit exister pour l'ordre d'enseignement choisi
          var mats = MATIERES[ordreDe(o.nom)]; if (!nv.matiere || mats.indexOf(nv.matiere) < 0) nv.matiere = mats[0];
        }
        ecrire(nv); fermer(); appliquer();
        if ((nv.groupe && nv.groupe !== DEFAUT.groupe)) avis('Maquette : le contenu affiché reste celui de la 4e année, groupe 41.');
      };
      m.appendChild(d);
    });
    document.body.appendChild(m);
    var r = span.getBoundingClientRect(), largeur = Math.min(320, window.innerWidth - 16);
    m.style.top = (window.scrollY + r.bottom + 6) + 'px';
    m.style.left = Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + window.innerWidth - largeur - 8)) + 'px';
    span.classList.add('ouvert');
  }

  document.addEventListener('click', function (e) {
    var s = e.target.closest && e.target.closest('.filtre span');
    if (s) { e.stopPropagation(); if (s.classList.contains('ouvert')) fermer(); else ouvrir(s); return; }
    if (!e.target.closest || !e.target.closest('.sdp-menu')) fermer();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') fermer(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', appliquer); else appliquer();
})();
