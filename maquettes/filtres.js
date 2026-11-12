/* Maquette : pastilles Niveau (et groupe), Matière, Étape, reliées au catalogue des savoirs (catalogue/).
   Le choix est gardé d'une page à l'autre et diffusé aux pages par l'événement « sdp:filtres ».
   Dans l'application, les groupes viendront de Microsoft 365 ou d'un import, et les matières de la tâche de l'enseignante. */
(function () {
  var CLE = 'sdp-filtres-v2';
  var NIVEAUX = [
    { ordre: 'primaire', niveau: '1', nom: '1re année' }, { ordre: 'primaire', niveau: '2', nom: '2e année' },
    { ordre: 'primaire', niveau: '3', nom: '3e année' }, { ordre: 'primaire', niveau: '4', nom: '4e année' },
    { ordre: 'primaire', niveau: '5', nom: '5e année' }, { ordre: 'primaire', niveau: '6', nom: '6e année' },
    { ordre: 'secondaire', niveau: '1', nom: '1re secondaire' }, { ordre: 'secondaire', niveau: '2', nom: '2e secondaire' },
    { ordre: 'secondaire', niveau: '3', nom: '3e secondaire' }, { ordre: 'secondaire', niveau: '4', nom: '4e secondaire' },
    { ordre: 'secondaire', niveau: '5', nom: '5e secondaire' }
  ];
  var ETAPES = ['Étape 1', 'Étape 2', 'Étape 3', 'Toute l’année'];
  var DEFAUT = { ordre: 'primaire', niveau: '4', matiere: '', etape: 'Étape 2' };   // matiere '' = toutes (primaire)

  var index = null, cache = {};
  function chargerIndex() {
    if (!index) index = fetch('catalogue/index.json').then(function (r) { return r.json(); }).then(function (j) { return j.disciplines; });
    return index;
  }
  function discipline(ordre, code) {
    return chargerIndex().then(function (ix) {
      var e = ix.filter(function (d) { return d.ordre === ordre && d.code === code; })[0];
      if (!e) return null;
      if (!cache[e.fichier]) cache[e.fichier] = fetch('catalogue/' + e.fichier).then(function (r) { return r.json(); });
      return cache[e.fichier];
    });
  }
  function matieres(ordre, niveau) {
    return chargerIndex().then(function (ix) { return ix.filter(function (d) { return d.ordre === ordre && d.niveaux.indexOf(niveau) >= 0; }); });
  }

  function lire() { try { var v = JSON.parse(localStorage.getItem(CLE)); return v && v.niveau ? v : JSON.parse(JSON.stringify(DEFAUT)); } catch (e) { return JSON.parse(JSON.stringify(DEFAUT)); } }
  function ecrire(v) { try { localStorage.setItem(CLE, JSON.stringify(v)); } catch (e) {} }
  function nomNiveau(v) { return NIVEAUX.filter(function (n) { return n.ordre === v.ordre && n.niveau === v.niveau; })[0].nom; }
  function nomGroupe(v) { return nomNiveau(v) + ', groupe ' + (v.ordre === 'primaire' ? v.niveau + '1' : v.niveau + '02'); }

  // Matière effective : au primaire, « Toutes les matières » donne le français pour les listes de savoirs.
  function etat() {
    var v = lire();
    return matieres(v.ordre, v.niveau).then(function (ms) {
      var m = ms.filter(function (d) { return d.code === v.matiere; })[0];
      if (!m && v.matiere) { v.matiere = ''; }
      var effective = m || ms.filter(function (d) { return d.code === 'FRA'; })[0] || ms[0];
      return { ordre: v.ordre, niveau: v.niveau, etape: v.etape, matiere: m || null, effective: effective,
               nomNiveau: nomNiveau(v), nomGroupe: nomGroupe(v), nomMatiere: m ? m.nom : (v.ordre === 'primaire' ? 'Toutes les matières' : effective.nom) };
    });
  }
  window.SDP = { etat: etat, discipline: discipline, matieres: matieres, chargerIndex: chargerIndex };

  var css = document.createElement('style');
  css.textContent = '.filtre span{cursor:pointer;user-select:none;position:relative}' +
    '.filtre span:after{content:"";display:inline-block;width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(45deg);margin:0 0 3px 9px;opacity:.55}' +
    '.filtre span.ouvert{border-color:var(--encre,#33302b)}' +
    '.sdp-menu{position:absolute;z-index:50;min-width:250px;max-width:340px;max-height:70vh;overflow:auto;background:#fffdf9;border:1px solid #ebe4d8;border-radius:12px;box-shadow:0 10px 30px rgba(51,48,43,.12);padding:6px;font-family:inherit;font-size:13px}' +
    '.sdp-menu div.o{padding:7px 10px;border-radius:8px;cursor:pointer;line-height:1.35}.sdp-menu div.o:hover{background:#f4f0e8}' +
    '.sdp-menu div.o.on{background:#efe9df;font-weight:500}.sdp-menu small{display:block;color:#8a8278;font-weight:400;font-size:12px}' +
    '.sdp-menu div.t{padding:10px 10px 4px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8a8278}' +
    '.sdp-menu div.t+div.o{margin-top:0}.sdp-menu div.t:not(:first-child){border-top:1px solid #ebe4d8;margin-top:4px}';
  document.head.appendChild(css);

  function fermer() { var m = document.querySelector('.sdp-menu'); if (m) m.remove(); document.querySelectorAll('.filtre span.ouvert').forEach(function (s) { s.classList.remove('ouvert'); }); }
  function genre(span) {
    if (span.dataset.genre) return span.dataset.genre;
    var t = span.textContent;
    return /groupe|année|secondaire/i.test(t) && !/^Toute/.test(t) ? 'groupe' : (/^Étape|^Toute l’année/.test(t) ? 'etape' : 'matiere');
  }

  function appliquer() {
    return etat().then(function (e) {
      document.querySelectorAll('.filtre span').forEach(function (s) {
        var g = genre(s); s.dataset.genre = g;
        s.textContent = g === 'groupe' ? e.nomGroupe : g === 'etape' ? e.etape : e.nomMatiere;
      });
      window.dispatchEvent(new CustomEvent('sdp:filtres', { detail: e }));
    });
  }

  function placer(m, span) {
    document.body.appendChild(m);
    var r = span.getBoundingClientRect(), largeur = Math.min(340, window.innerWidth - 16);
    m.style.top = (window.scrollY + r.bottom + 6) + 'px';
    m.style.left = Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + window.innerWidth - largeur - 8)) + 'px';
    span.classList.add('ouvert');
  }
  function option(m, nom, detail, actif, choisir) {
    var d = document.createElement('div'); d.className = 'o' + (actif ? ' on' : '');
    d.textContent = nom; if (detail) { var s = document.createElement('small'); s.textContent = detail; d.appendChild(s); }
    d.onclick = function (ev) { ev.stopPropagation(); choisir(); fermer(); appliquer(); };
    m.appendChild(d);
  }
  function titre(m, t) { var d = document.createElement('div'); d.className = 't'; d.textContent = t; m.appendChild(d); }

  function ouvrir(span) {
    fermer();
    var v = lire(), g = genre(span), m = document.createElement('div'); m.className = 'sdp-menu';
    if (g === 'groupe') {
      ['primaire', 'secondaire'].forEach(function (o) {
        titre(m, o === 'primaire' ? 'Primaire' : 'Secondaire');
        NIVEAUX.filter(function (n) { return n.ordre === o; }).forEach(function (n) {
          option(m, n.nom, null, v.ordre === n.ordre && v.niveau === n.niveau, function () {
            var nv = lire(); nv.ordre = n.ordre; nv.niveau = n.niveau; ecrire(nv);
          });
        });
      });
      placer(m, span);
    } else if (g === 'etape') {
      ETAPES.forEach(function (x) { option(m, x, null, v.etape === x, function () { var nv = lire(); nv.etape = x; ecrire(nv); }); });
      placer(m, span);
    } else {
      matieres(v.ordre, v.niveau).then(function (ms) {
        if (v.ordre === 'primaire') option(m, 'Toutes les matières', 'Titulaire', !v.matiere, function () { var nv = lire(); nv.matiere = ''; ecrire(nv); });
        ms.forEach(function (d) {
          option(m, d.nom, d.n + ' savoirs dans la PDA' + (d.variantes && d.variantes[v.niveau] ? ' · ' + d.variantes[v.niveau].join(', ') : ''), v.matiere === d.code, function () {
            var nv = lire(); nv.matiere = d.code; ecrire(nv);
          });
        });
        placer(m, span);
      });
    }
  }

  document.addEventListener('click', function (e) {
    var s = e.target.closest && e.target.closest('.filtre span');
    if (s) { e.stopPropagation(); if (s.classList.contains('ouvert')) fermer(); else ouvrir(s); return; }
    if (!e.target.closest || !e.target.closest('.sdp-menu')) fermer();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') fermer(); });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', appliquer); else appliquer();
})();
