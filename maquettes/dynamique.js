/* Maquette : blocs construits à partir du catalogue des savoirs, selon le niveau et la matière choisis.
   - [data-sdp=resume]   : « 3e secondaire, groupe 302 · Histoire du Québec et du Canada · Étape 2 »
   - liste .sv des assistants de Créer : savoirs de la PDA pour l'année, filtres et recherche
   - [data-sdp=contenus] : contenus à couvrir (Planifier)
   - [data-sdp=idee]     : « Partir d'une idée », savoirs reliés à la description
   - body[data-echantillon] : avis sur l'aperçu quand la sélection diffère de l'exemple illustré */
(function () {
  var NOM = { A: 'flèche', M: 'étoile', R: 'case bleue', P: 'au programme' };
  var BADGE = { A: ['ap', 'Apprentissage'], M: ['ma', 'Maîtrise attendue'], R: ['re', 'Réinvestissement'], P: ['pr', 'Au programme'] };
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function statut(p) {
    if (!p) return '';
    if (typeof p === 'string') return NOM[p];
    return Object.keys(p).map(function (k) { return k + ' : ' + NOM[p[k]]; }).join(' · ');
  }
  function principal(p) { if (typeof p === 'string') return p; var v = Object.keys(p).map(function (k) { return p[k]; }); return v.indexOf('M') >= 0 ? 'M' : v.indexOf('A') >= 0 ? 'A' : v[0]; }
  function badge(p) { var b = BADGE[principal(p)]; var det = typeof p === 'string' ? b[1] : statut(p); return '<span class="b ' + b[0] + '">' + esc(det) + '</span>'; }
  function norm(t) { return t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ' '); }
  var css = document.createElement('style');
  css.textContent = '.b.pr{background:#efe9f4;color:#6d6292}.sdp-outils{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}' +
    '.sdp-outils select,.sdp-outils input{font:inherit;font-size:13px;border:1px solid var(--ligne,#ebe4d8);border-radius:20px;padding:6px 12px;background:#fffefb;color:inherit;max-width:100%}' +
    '.sdp-outils input{flex:1;min-width:160px}.sdp-plus{margin-top:10px;font-size:12.5px;color:var(--doux,#8a8278)}.sdp-plus a{cursor:pointer;text-decoration:underline;text-underline-offset:3px}' +
    '.sdp-vide{padding:14px 0;color:var(--doux,#8a8278);font-size:13px}.sdp-avis-apercu{margin:0 0 10px;padding:8px 10px;border-radius:8px;background:#f4f1f8;color:#5b5276;font-size:12px}' +
    'label.sv{cursor:pointer}';
  document.head.appendChild(css);

  function savoirsAnnee(e) {
    return window.SDP.discipline(e.ordre, e.effective.code).then(function (d) {
      if (!d) return [];
      // l'année d'abord : à maîtriser, à apprendre, au programme, puis à réinvestir (ordre du document conservé)
      var rang = { M: 0, A: 1, P: 2, R: 3 };
      return d.savoirs.map(function (s, i) { return [s, i]; }).filter(function (x) { return x[0].p[e.niveau]; })
        .sort(function (a, b) { return (rang[principal(a[0].p[e.niveau])] - rang[principal(b[0].p[e.niveau])]) || (a[1] - b[1]); })
        .map(function (x) { return x[0]; });
    });
  }

  // ---- résumé sous le titre
  function resume(e) {
    document.querySelectorAll('[data-sdp=resume]').forEach(function (el) {
      el.textContent = e.nomGroupe + ' · ' + (el.dataset.matiere === 'effective' ? e.effective.nom : e.nomMatiere) + ' · ' + e.etape + (el.dataset.suffixe ? ' · ' + el.dataset.suffixe : '');
    });
  }

  // ---- liste de savoirs des assistants
  var etatListe = { section: '', statut: '', q: '', max: 12, coches: {} };
  function listeSavoirs(e, sv) {
    var premiere = document.querySelector('label.sv'); if (!premiere) return;
    var zone = document.querySelector('.sdp-savoirs');
    if (!zone) {
      zone = document.createElement('div'); zone.className = 'sdp-savoirs';
      var titre = premiere.previousElementSibling && premiere.previousElementSibling.classList.contains('gtitre') ? premiere.previousElementSibling : null;
      premiere.parentNode.insertBefore(zone, premiere);
      var n = zone.nextElementSibling;   // retirer la liste illustrée (savoirs consécutifs)
      while (n && (n.tagName === 'LABEL' && n.classList.contains('sv'))) { var x = n.nextElementSibling; n.remove(); n = x; }
      document.querySelectorAll('label.sv').forEach(function (l) { if (!zone.contains(l)) l.remove(); });
      document.querySelectorAll('.gtitre').forEach(function (g) { if (/^Accord du verbe/.test(g.textContent)) g.remove(); });
      zone._titre = titre;
    }
    var sections = []; sv.forEach(function (s) { var k = s.g || s.s; if (k && sections.indexOf(k) < 0) sections.push(k); });
    function rendre() {
      var q = norm(etatListe.q).split(/\s+/).filter(Boolean);
      var liste = sv.filter(function (s) {
        return (!etatListe.section || (s.g || s.s) === etatListe.section) && (!etatListe.statut || principal(s.p[e.niveau]) === etatListe.statut) &&
          q.every(function (m) { return norm(s.t + ' ' + s.s + ' ' + s.id).indexOf(m) >= 0; });
      });
      var h = '<div class="sdp-outils"><select data-k="section"><option value="">Toutes les sections (' + sections.length + ')</option>' +
        sections.map(function (x) { return '<option' + (x === etatListe.section ? ' selected' : '') + ' value="' + esc(x) + '">' + esc(x.length > 70 ? x.slice(0, 68) + '…' : x) + '</option>'; }).join('') + '</select>' +
        '<select data-k="statut"><option value="">Tous les statuts</option>' + ['A', 'M', 'R', 'P'].filter(function (k) { return sv.some(function (s) { return principal(s.p[e.niveau]) === k; }); })
          .map(function (k) { return '<option value="' + k + '"' + (etatListe.statut === k ? ' selected' : '') + '>' + BADGE[k][1] + '</option>'; }).join('') + '</select>' +
        '<input data-k="q" placeholder="Rechercher un savoir…" value="' + esc(etatListe.q) + '"></div>';
      if (!liste.length) h += '<div class="sdp-vide">Aucun savoir ne correspond.</div>';
      liste.slice(0, etatListe.max).forEach(function (s) {
        var on = etatListe.coches[s.id];
        h += '<label class="sv' + (on ? ' on' : '') + '" data-id="' + esc(s.id) + '"><span class="box">' + (on ? '✓' : '') + '</span><div class="svt">' + esc(s.t) +
          (s.s ? '<div style="font-size:11.5px;color:var(--doux);margin-top:2px">' + esc(s.s) + '</div>' : '') + '</div><div class="svb">' + badge(s.p[e.niveau]) + '<span class="id">' + esc(s.id) + '</span></div></label>';
      });
      h += '<div class="sdp-plus">' + liste.length + ' savoirs pour la ' + esc(e.nomNiveau) + ' en ' + esc(e.effective.nom) + (liste.length > etatListe.max ? ' · <a data-plus>en afficher plus</a>' : '') + '</div>';
      zone.innerHTML = h;
      if (zone._titre) zone._titre.textContent = 'Savoirs de la PDA · ' + e.effective.nom + ' · ' + e.nomNiveau;
      zone.querySelectorAll('select,input').forEach(function (c) {
        c.addEventListener(c.tagName === 'INPUT' ? 'input' : 'change', function () { etatListe[c.dataset.k] = c.value; etatListe.max = 12; var pos = c.tagName === 'INPUT' ? c.selectionStart : null; rendre(); if (pos !== null) { var i = zone.querySelector('input'); i.focus(); i.setSelectionRange(pos, pos); } });
      });
      zone.querySelectorAll('label.sv').forEach(function (l) { l.addEventListener('click', function (ev) { ev.preventDefault(); var id = l.dataset.id; etatListe.coches[id] = !etatListe.coches[id]; rendre(); }); });
      var p = zone.querySelector('[data-plus]'); if (p) p.onclick = function () { etatListe.max += 24; rendre(); };
    }
    rendre();
  }

  // ---- contenus à couvrir (Planifier)
  function contenus(e, sv) {
    document.querySelectorAll('[data-sdp=contenus]').forEach(function (c) {
      var a = sv.filter(function (s) { var p = principal(s.p[e.niveau]); return p === 'A' || p === 'M' || p === 'P'; });
      var h = '<h2>Contenus à couvrir · ' + esc(e.effective.nom) + ' · ' + esc(e.nomNiveau) + '</h2><p class="sous">Tirés de la Progression des apprentissages : ' + a.length + ' savoirs à faire apprendre ou à faire maîtriser cette année' +
        (sv.length > a.length ? ', ' + (sv.length - a.length) + ' à réinvestir' : '') + '.</p>';
      a.slice(0, 8).forEach(function (s, i) {
        var et = i < 2 ? ['e-vu', 'Vu'] : i < 4 ? ['e-cours', 'En cours'] : ['e-venir', 'À venir'];
        h += '<div class="contenu"><div><span class="code">' + esc(s.id) + '</span>' + esc(s.t) + '<small>' + esc(s.s || s.g) + '</small></div><div><span class="sym">' + esc(statut(s.p[e.niveau])) + '</span> <span class="etat ' + et[0] + '">' + et[1] + '</span></div></div>';
      });
      if (a.length > 8) h += '<div class="sdp-plus">et ' + (a.length - 8) + ' autres · <a href="creer-fiche.html">créer du matériel sur ces savoirs</a></div>';
      c.innerHTML = h;
    });
  }

  // ---- Partir d'une idée
  function idee(e, sv) {
    document.querySelectorAll('[data-sdp=idee]').forEach(function (c) {
      var ta = c.querySelector('textarea'), res = c.querySelector('.sdp-lies'), titre = c.querySelector('.lies');
      if (!res) { res = document.createElement('div'); res.className = 'sdp-lies'; var vieux = c.querySelectorAll('.lie'); if (vieux.length) { vieux[0].parentNode.insertBefore(res, vieux[0]); vieux.forEach(function (v) { v.remove(); }); } }
      function chercher() {
        var mots = norm(ta.value).split(/\s+/).filter(function (m) { return m.length > 3; });
        var scores = sv.map(function (s) { var t = norm(s.t + ' ' + s.s); var n = 0; mots.forEach(function (m) { if (t.indexOf(m.slice(0, Math.max(5, m.length - 2))) >= 0) n++; }); return [n, s]; })
          .filter(function (x) { return x[0] > 0; }).sort(function (a, b) { return b[0] - a[0]; }).slice(0, 3);
        if (titre) titre.textContent = 'Savoirs de la PDA reliés (' + e.effective.nom + ', ' + e.nomNiveau + ')';
        res.innerHTML = scores.length ? scores.map(function (x) { return '<div class="lie"><span class="code">' + esc(x[1].id) + '</span>' + esc(x[1].t) + '<span class="sym">' + esc(statut(x[1].p[e.niveau])) + '</span></div>'; }).join('')
          : '<div class="sdp-vide">Décrivez votre idée : les savoirs correspondants s’affichent ici.</div>';
      }
      if (!ta._lie) { ta.addEventListener('input', chercher); ta._lie = true; }
      chercher();
    });
  }

  // ---- avis sur les aperçus d'exemple
  function apercu(e) {
    var ech = document.body.dataset.echantillon; if (!ech) return;
    var p = ech.split('|'), meme = p[0] === e.ordre && p[1] === e.niveau && p[2] === e.effective.code;
    // éléments propres à l'exemple illustré : suggestions et filtres fixes masqués quand la sélection change
    document.querySelectorAll('.sugg, .filtres').forEach(function (x) { x.style.display = meme ? '' : 'none'; });
    document.querySelectorAll('.apercu, .diapos, [data-exemple]').forEach(function (a) {
      var av = a.previousElementSibling && a.previousElementSibling.classList.contains('sdp-avis-apercu') ? a.previousElementSibling : null;
      if (meme) { if (av) av.remove(); return; }
      if (!av) { av = document.createElement('div'); av.className = 'sdp-avis-apercu'; a.parentNode.insertBefore(av, a); }
      av.textContent = 'Aperçu d’exemple (' + document.body.dataset.echantillonNom + '). Dans l’application, il est créé à partir des savoirs cochés en ' + e.effective.nom + ', ' + e.nomNiveau + '.';
    });
  }

  window.addEventListener('sdp:filtres', function (ev) {
    var e = ev.detail; resume(e); apercu(e);
    etatListe = { section: '', statut: '', q: '', max: 12, coches: {} };
    savoirsAnnee(e).then(function (sv) { listeSavoirs(e, sv); contenus(e, sv); idee(e, sv); });
  });
})();
