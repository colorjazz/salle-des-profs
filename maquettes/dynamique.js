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
  // Libellé lisible : sans marqueur de liste ; un fragment (« dét. + nom ») reprend son parent
  function sansMarque(x) { return String(x || '').replace(/^\s*(?:[A-Z]|\d{1,2}(?:\.\d+)*|[a-z]|[ivx]+)\.\s+/, '').replace(/\s*\(P\d[^)]*\)/g, '').trim(); }
  function majuscule(x) { return x ? x.charAt(0).toUpperCase() + x.slice(1) : x; }
  function libelle(s) {
    if (s.l) return s.l;   // libellé rédigé (Gemini), quand il existe
    var t = sansMarque(s.t), parties = (s.s || '').split(' › ').map(sansMarque).filter(Boolean);
    var parent = parties[parties.length - 1] || '';
    if (parent && (/^[a-zà-ü(]/.test(t) || t.length < 28) && parent.length < 110) return majuscule(parent.replace(/\s*:\s*$/, '')) + ' : ' + t;
    return majuscule(t);
  }
  function contexte(s) { var parties = (s.s || '').split(' › ').map(sansMarque).filter(Boolean); return parties.length > 1 ? majuscule(parties[0]) : ''; }
  function norm(t) { return t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ' '); }
  var css = document.createElement('style');
  css.textContent = '.b.pr{background:#efe9f4;color:#6d6292}.sdp-outils{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}' +
    '.sdp-outils select,.sdp-outils input{font:inherit;font-size:13px;border:1px solid var(--ligne,#ebe4d8);border-radius:20px;padding:6px 12px;background:#fffefb;color:inherit;max-width:100%}' +
    '.sdp-outils input{flex:1;min-width:160px}.sdp-plus{margin-top:10px;font-size:12.5px;color:var(--doux,#8a8278)}.sdp-plus a{cursor:pointer;text-decoration:underline;text-underline-offset:3px}' +
    '.sdp-vide{padding:14px 0;color:var(--doux,#8a8278);font-size:13px}.sdp-avis-apercu{margin:0 0 10px;padding:8px 10px;border-radius:8px;background:#f4f1f8;color:#5b5276;font-size:12px}' +
    'label.sv{cursor:pointer}' +
    '.sdp-mods{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin-bottom:12px}' +
    '.sdp-mod{border:1px solid var(--ligne,#ebe4d8);border-radius:12px;padding:12px 14px;background:#fffefb;cursor:pointer;text-align:left;font:inherit;color:inherit}' +
    '.sdp-mod:hover{border-color:var(--lavande,#9a8fb5);background:#f9f7fc}.sdp-mod b{display:block;font-weight:500;font-size:14px;margin-bottom:3px}' +
    '.sdp-mod p{margin:0 0 8px;font-size:12px;color:var(--doux,#8a8278);line-height:1.4}.sdp-mod small{font-size:11.5px;color:var(--doux,#8a8278)}' +
    '.sdp-mod .barre{display:flex;height:4px;border-radius:2px;overflow:hidden;gap:1px;margin-top:6px;background:#efe9de}.sdp-mod .barre i{display:block}' +
    '.sdp-retour{display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:8px}.sdp-retour a{cursor:pointer;font-size:12.5px;color:var(--doux,#8a8278);text-decoration:underline;text-underline-offset:3px}' +
    '.sdp-retour b{font-weight:500;font-size:15px}.sdp-desc{font-size:12.5px;color:var(--doux,#8a8278);margin:0 0 10px}';
  document.head.appendChild(css);

  var modulesCache = {};
  function modules(e) {
    var f = e.effective.fichier;
    if (!modulesCache[f]) modulesCache[f] = fetch('catalogue/modules/' + f).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
    return modulesCache[f];
  }
  function savoirsAnnee(e) {
    return Promise.all([window.SDP.discipline(e.ordre, e.effective.code), modules(e)]).then(function (res) {
      var d = res[0], m = res[1];
      if (d && m) { e.modules = m.modules; d.savoirs.forEach(function (s) { s.m = m.affectation[s.id]; if (m.libelles && m.libelles[s.id]) s.l = m.libelles[s.id]; }); } else { e.modules = null; }
      return d;
    }).then(function (d) {
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
  var etatListe = { module: '', statut: '', q: '', max: 12, coches: {} };
  var COUL = { M: '#c79a7e', A: '#e3cf9f', P: '#b9add6', R: '#b6c8de' };
  function compte(liste, niveau) { var c = { M: 0, A: 0, P: 0, R: 0 }; liste.forEach(function (s) { c[principal(s.p[niveau])]++; }); return c; }
  function resumeCompte(c) {
    var parts = []; if (c.M) parts.push(c.M + ' à maîtriser'); if (c.A) parts.push(c.A + ' à apprendre'); if (c.P) parts.push(c.P + ' au programme'); if (c.R) parts.push(c.R + ' à réinvestir');
    return parts.join(' · ');
  }
  function barre(c, n) { return '<div class="barre">' + ['M', 'A', 'P', 'R'].filter(function (k) { return c[k]; }).map(function (k) { return '<i style="width:' + (100 * c[k] / n) + '%;background:' + COUL[k] + '"></i>'; }).join('') + '</div>'; }
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
    var mods = (e.modules || []).map(function (m) { return { m: m, sv: sv.filter(function (s) { return s.m === m.id; }) }; }).filter(function (x) { return x.sv.length; });
    function rendre() {
      var q = norm(etatListe.q).split(/\s+/).filter(Boolean);
      var mod = mods.filter(function (x) { return x.m.id === etatListe.module; })[0];
      var h = '';
      if (!mod && !q.length && mods.length) {   // vue d'ensemble : une carte par module
        h += '<div class="sdp-outils"><input data-k="q" placeholder="Ou cherchez un savoir précis…" value=""></div><div class="sdp-mods">' +
          mods.map(function (x) { var c = compte(x.sv, e.niveau); return '<button class="sdp-mod" data-mod="' + esc(x.m.id) + '"><b>' + esc(x.m.titre) + '</b>' + (x.m.description ? '<p>' + esc(x.m.description) + '</p>' : '') +
            '<small>' + x.sv.length + ' savoir' + (x.sv.length > 1 ? 's' : '') + ' · ' + esc(resumeCompte(c)) + '</small>' + barre(c, x.sv.length) + '</button>'; }).join('') + '</div>' +
          '<div class="sdp-plus">' + mods.length + ' modules · ' + sv.length + ' savoirs de la PDA pour la ' + esc(e.nomNiveau) + ' en ' + esc(e.effective.nom) + '</div>';
        zone.innerHTML = h; brancher(); if (zone._titre) zone._titre.textContent = 'Choisissez un module · ' + e.effective.nom + ' · ' + e.nomNiveau; return;
      }
      var base = mod ? mod.sv : sv;
      var liste = base.filter(function (s) {
        return (!etatListe.statut || principal(s.p[e.niveau]) === etatListe.statut) && q.every(function (m) { return norm(s.t + ' ' + s.s + ' ' + s.id).indexOf(m) >= 0; });
      });
      if (mods.length) h += '<div class="sdp-retour"><b>' + esc(mod ? mod.m.titre : 'Recherche dans tous les modules') + '</b><a data-retour>← Tous les modules</a></div>' + (mod && mod.m.description ? '<p class="sdp-desc">' + esc(mod.m.description) + '</p>' : '');
      h += '<div class="sdp-outils">' +
        '<select data-k="statut"><option value="">Tous les statuts</option>' + ['A', 'M', 'R', 'P'].filter(function (k) { return sv.some(function (s) { return principal(s.p[e.niveau]) === k; }); })
          .map(function (k) { return '<option value="' + k + '"' + (etatListe.statut === k ? ' selected' : '') + '>' + BADGE[k][1] + '</option>'; }).join('') + '</select>' +
        '<input data-k="q" placeholder="Rechercher un savoir…" value="' + esc(etatListe.q) + '"></div>';
      if (!liste.length) h += '<div class="sdp-vide">Aucun savoir ne correspond.</div>';
      liste.slice(0, etatListe.max).forEach(function (s) {
        var on = etatListe.coches[s.id];
        h += '<label class="sv' + (on ? ' on' : '') + '" data-id="' + esc(s.id) + '"><span class="box">' + (on ? '✓' : '') + '</span><div class="svt">' + esc(libelle(s)) +
          (contexte(s) ? '<div style="font-size:11.5px;color:var(--doux);margin-top:2px">' + esc(contexte(s)) + '</div>' : '') + '</div><div class="svb">' + badge(s.p[e.niveau]) + '<span class="id">' + esc(s.id) + '</span></div></label>';
      });
      h += '<div class="sdp-plus">' + liste.length + ' savoirs pour la ' + esc(e.nomNiveau) + ' en ' + esc(e.effective.nom) + (liste.length > etatListe.max ? ' · <a data-plus>en afficher plus</a>' : '') + '</div>';
      zone.innerHTML = h; brancher();
      if (zone._titre) zone._titre.textContent = 'Savoirs de la PDA · ' + e.effective.nom + ' · ' + e.nomNiveau;
    }
    function brancher() {
      zone.querySelectorAll('[data-mod]').forEach(function (b) { b.onclick = function (ev) { ev.preventDefault(); etatListe.module = b.dataset.mod; etatListe.q = ''; etatListe.max = 12; rendre(); }; });
      var r = zone.querySelector('[data-retour]'); if (r) r.onclick = function () { etatListe.module = ''; etatListe.q = ''; etatListe.statut = ''; rendre(); };
      zone.querySelectorAll('select,input').forEach(function (c) {
        c.addEventListener(c.tagName === 'INPUT' ? 'input' : 'change', function () { etatListe[c.dataset.k] = c.value; etatListe.max = 12; var pos = c.tagName === 'INPUT' ? c.selectionStart : null; rendre(); if (pos !== null) { var i = zone.querySelector('input'); i.focus(); i.setSelectionRange(pos, pos); } });
      });
      zone.querySelectorAll('label.sv').forEach(function (l) { l.addEventListener('click', function (ev) { ev.preventDefault(); var id = l.dataset.id; etatListe.coches[id] = !etatListe.coches[id]; rendre(); }); });
      var p = zone.querySelector('[data-plus]'); if (p) p.onclick = function () { etatListe.max += 24; rendre(); };
    }
    rendre();
  }

  // ---- contenus à couvrir (Planifier) : par module
  function contenus(e, sv) {
    document.querySelectorAll('[data-sdp=contenus]').forEach(function (c) {
      var mods = (e.modules || []).map(function (m) { return { m: m, sv: sv.filter(function (s) { return s.m === m.id; }) }; }).filter(function (x) { return x.sv.length; });
      var h = '<h2>Contenus à couvrir · ' + esc(e.effective.nom) + ' · ' + esc(e.nomNiveau) + '</h2><p class="sous">' + mods.length + ' modules, ' + sv.length + ' savoirs de la Progression des apprentissages. Cliquez sur un module pour créer du matériel.</p>';
      mods.forEach(function (x, i) {
        var cpt = compte(x.sv, e.niveau), et = i < 2 ? ['e-vu', 'Vu'] : i < 4 ? ['e-cours', 'En cours'] : ['e-venir', 'À venir'];
        h += '<div class="contenu"><div><b style="font-weight:500">' + esc(x.m.titre) + '</b><small>' + esc(x.m.description || '') + '</small><small>' + x.sv.length + ' savoirs · ' + esc(resumeCompte(cpt)) + '</small></div><div><span class="etat ' + et[0] + '">' + et[1] + '</span></div></div>';
      });
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
        res.innerHTML = scores.length ? scores.map(function (x) { return '<div class="lie"><span class="code">' + esc(x[1].id) + '</span>' + esc(libelle(x[1])) + '<span class="sym">' + esc(statut(x[1].p[e.niveau])) + '</span></div>'; }).join('')
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
    document.querySelectorAll('.sugg').forEach(function (x) { x.style.display = meme ? '' : 'none'; });
    document.querySelectorAll('.filtres').forEach(function (x) { x.style.display = 'none'; });   // remplacés par les modules
    document.querySelectorAll('.apercu, .diapos, [data-exemple]').forEach(function (a) {
      var av = a.previousElementSibling && a.previousElementSibling.classList.contains('sdp-avis-apercu') ? a.previousElementSibling : null;
      if (meme) { if (av) av.remove(); return; }
      if (!av) { av = document.createElement('div'); av.className = 'sdp-avis-apercu'; a.parentNode.insertBefore(av, a); }
      av.textContent = 'Aperçu d’exemple (' + document.body.dataset.echantillonNom + '). Dans l’application, il est créé à partir des savoirs cochés en ' + e.effective.nom + ', ' + e.nomNiveau + '.';
    });
  }

  window.addEventListener('sdp:filtres', function (ev) {
    var e = ev.detail; resume(e); apercu(e);
    etatListe = { module: '', statut: '', q: '', max: 12, coches: {} };
    savoirsAnnee(e).then(function (sv) { listeSavoirs(e, sv); contenus(e, sv); idee(e, sv); });
  });
})();
