/* Cultures original asset library - static list/search app (no server, no framework).
   Each list page defines window.PAGE = {root, title, crumbs, rows, cols, filters, prev, next, sections}
   in its index_data.js; this script renders search, filters, thumbnails and pagination. */
(function () {
  'use strict';
  var P = window.PAGE || {};
  var ROOT = P.root || '';
  var PER = 60;
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function url(p) { if (!p) return ''; if (/^[A-Za-z]:\\/.test(p)) return 'file:///' + encodeURI(p.replace(/\\/g, '/')); return ROOT + encodeURI(p).replace(/#/g, '%23').replace(/%23([^/]*)$/, '#$1'); }
  function href(p) { if (!p) return ''; var i = p.indexOf('#'); if (i < 0) return url(p); return url(p.slice(0, i)) + '#' + encodeURI(p.slice(i + 1)); }
  var IDW = {good: 1, gfxhouse: 1, gfx: 1, bob: 1, atomic: 1, job: 1, logic: 1, vehicletype: 1, tribe: 1};
  /* query -> list of matchers; '<id word> <number>' becomes one whole-number phrase, other numbers match as whole numbers */
  function tokens(q) {
    var w = q.toLowerCase().split(/\s+/).filter(Boolean), out = [];
    for (var i = 0; i < w.length; i++) {
      if (IDW[w[i]] && i + 1 < w.length && /^\d+$/.test(w[i + 1])) { out.push(new RegExp('(^|[^a-z0-9])' + w[i] + ' ' + w[i + 1] + '(?![0-9])')); i++; }
      else if (/^\d+$/.test(w[i])) out.push(new RegExp('(^|[^0-9])' + w[i] + '(?![0-9])'));
      else out.push(w[i]);
    }
    return out;
  }
  function hit(s, t) { return typeof t === 'string' ? s.indexOf(t) >= 0 : t.test(s); }
  function rowText(r) {
    if (!r._t) { var a = []; for (var k in r) if (k[0] !== '_') a.push(r[k]); r._t = a.join(' ').toLowerCase(); }
    return r._t;
  }
  function thumb(r) {
    var t = r.THUMB; if (!t) return '<div class="nothumb">no preview</div>';
    if (r.THUMB_RECT) {
      var q = r.THUMB_RECT; if (typeof q === 'string') { try { q = JSON.parse(q); } catch (e) { q = null; } }
      if (q && q.length === 4) {
        var s = Math.min(1, 96 / Math.max(q[2], q[3], 1));
        return '<div class="crop" style="width:' + Math.ceil(q[2] * s) + 'px;height:' + Math.ceil(q[3] * s) + 'px"><div style="width:' + q[2] + 'px;height:' + q[3] +
          'px;transform:scale(' + s + ');transform-origin:0 0;background:url(\'' + url(t) + '\') -' + q[0] + 'px -' + q[1] + 'px"></div></div>';
      }
    }
    if (/\.(png|gif|jpe?g|bmp)$/i.test(t)) return '<a href="' + url(t) + '"><img loading="lazy" src="' + url(t) + '" alt=""></a>';
    return '<div class="nothumb">' + esc(t.split(/[\\/]/).pop()) + '</div>';
  }
  function linkset(r) {
    var L = [];
    if (r.DETAIL_PAGE) L.push('<a href="' + href(r.DETAIL_PAGE) + '">details</a>');
    if (r.OUTPUT && r.OUTPUT !== r.THUMB) L.push('<a href="' + url(r.OUTPUT) + '">output</a>');
    if (r.THUMB) L.push('<a href="' + url(r.THUMB) + '">image</a>');
    if (r.METADATA) L.push('<a href="' + url(r.METADATA) + '">metadata</a>');
    if (r.ATLAS) L.push('<a href="' + href('Shared/SourceLibraries/viewer.html#' + (r.BMD || '').toLowerCase()) + '">atlas</a>');
    if (r.AUDIO) L.push('<audio controls preload="none" src="' + url(r.AUDIO) + '"></audio>');
    return L.join(' ');
  }
  function crumbs() {
    var c = (P.crumbs || []).map(function (x) { return x[1] ? '<a href="' + url(x[1]) + '">' + esc(x[0]) + '</a>' : esc(x[0]); }).join(' / ');
    var nav = '';
    if (P.prev) nav += ' <a class="nav" href="' + url(P.prev[1]) + '">&larr; ' + esc(P.prev[0]) + '</a>';
    if (P.next) nav += ' <a class="nav" href="' + url(P.next[1]) + '">' + esc(P.next[0]) + ' &rarr;</a>';
    return '<nav class="crumbs">' + c + nav + '</nav>';
  }
  function list(el) {
    var rows = P.rows || [], cols = P.cols || [], filt = P.filters || [];
    var state = {q: '', f: {}, page: 0};
    var h = location.hash.replace(/^#/, '');
    h.split('&').forEach(function (kv) { var p = kv.split('='); if (p[0] === 'q' && p[1]) state.q = decodeURIComponent(p.slice(1).join('=')); });
    var ui = '<div class="bar"><input id="q" type="search" placeholder="Filter ' + rows.length + ' rows (all words must match)" value="' + esc(state.q) + '">';
    filt.forEach(function (f) {
      var vals = {}; rows.forEach(function (r) { var v = r[f]; if (v !== '' && v != null) vals[v] = (vals[v] || 0) + 1; });
      ui += ' <select data-f="' + f + '"><option value="">' + esc(f.replace(/_/g, ' ').toLowerCase()) + ': all</option>' +
        Object.keys(vals).sort().map(function (v) { return '<option value="' + esc(v) + '">' + esc(v) + ' (' + vals[v] + ')</option>'; }).join('') + '</select>';
    });
    ui += '</div><div id="count"></div><div id="pager1" class="pager"></div><table class="grid"><thead><tr><th>preview</th>' +
      cols.map(function (c) { return '<th>' + esc(c.replace(/_/g, ' ').toLowerCase()) + '</th>'; }).join('') + '<th>links</th></tr></thead><tbody id="tb"></tbody></table><div id="pager2" class="pager"></div>';
    el.innerHTML = ui;
    var q = document.getElementById('q');
    function matches() {
      var t = tokens(state.q);
      return rows.filter(function (r) {
        for (var f in state.f) if (state.f[f] && String(r[f]) !== state.f[f]) return false;
        if (!t.length) return true;
        var s = rowText(r); for (var i = 0; i < t.length; i++) if (!hit(s, t[i])) return false; return true;
      });
    }
    function render() {
      var m = matches(), n = Math.max(1, Math.ceil(m.length / PER));
      if (state.page >= n) state.page = n - 1;
      var part = m.slice(state.page * PER, state.page * PER + PER);
      document.getElementById('count').textContent = m.length + ' of ' + rows.length + ' rows';
      document.getElementById('tb').innerHTML = part.map(function (r) {
        return '<tr id="' + esc(r.ASSET_ID) + '"><td class="th">' + thumb(r) + '</td>' + cols.map(function (c) {
          var v = r[c]; return '<td class="c-' + c + '">' + esc(v) + '</td>'; }).join('') + '<td class="links">' + linkset(r) + '</td></tr>'; }).join('');
      var pg = n > 1 ? '<button data-p="-1">&larr; prev</button> page ' + (state.page + 1) + ' / ' + n + ' <button data-p="1">next &rarr;</button>' : '';
      document.getElementById('pager1').innerHTML = pg; document.getElementById('pager2').innerHTML = pg;
    }
    el.addEventListener('click', function (e) { var b = e.target.closest('button[data-p]'); if (b) { state.page += +b.dataset.p; if (state.page < 0) state.page = 0; render(); window.scrollTo(0, el.offsetTop); } });
    q.addEventListener('input', function () { state.q = q.value; state.page = 0; history.replaceState(null, '', '#q=' + encodeURIComponent(state.q)); render(); });
    window.addEventListener('hashchange', function () { var m = location.hash.match(/q=([^&]*)/); if (m) { state.q = decodeURIComponent(m[1]); q.value = state.q; state.page = 0; render(); } });
    el.querySelectorAll('select[data-f]').forEach(function (s) { s.addEventListener('change', function () { state.f[s.dataset.f] = s.value; state.page = 0; render(); }); });
    render();
  }
  function search(el) {
    el.innerHTML = '<div class="bar"><input id="gq" type="search" placeholder="Search the whole library: names, IDs (Good 31, GfxHouse 5, BOB 101, atomic 15), BMD files, BobSeq names..."></div><div id="gres"></div>';
    var gq = document.getElementById('gq'), out = document.getElementById('gres'), loaded = false, timer = null;
    function run() {
      var t = tokens(gq.value); if (!t.length) { out.innerHTML = ''; return; }
      var D = window.SEARCHDB || {rows: []}, R = D.rows, hits = [], cats = {};
      for (var i = 0; i < R.length; i++) {
        var s = R[i][2], ok = true; for (var j = 0; j < t.length; j++) if (!hit(s, t[j])) { ok = false; break; }
        if (ok) { var cn = D.cats[R[i][3]]; cats[cn] = (cats[cn] || 0) + 1; if (hits.length < 300) hits.push(R[i]); }
      }
      var total = 0; for (var c in cats) total += cats[c];
      out.innerHTML = '<p>' + total + ' matches' + (total > 300 ? ' (first 300 shown)' : '') + ': ' + Object.keys(cats).sort().map(function (c) { return esc(c) + ' ' + cats[c]; }).join(' | ') + '</p>' +
        '<table class="grid"><tbody>' + hits.map(function (r) {
          return '<tr><td class="th">' + thumb({THUMB: r[7] >= 0 ? D.paths[r[7]] : '', THUMB_RECT: r[8]}) + '</td><td><a href="' + href(D.paths[r[6]] + (r[9] === 1 ? '#' + r[0] : r[9] === 2 ? '#q=' + r[0] : '')) + '">' + esc(r[1] || r[0]) + '</a><div class="sub">' + esc(r[0]) +
            '</div></td><td>' + esc(D.cats[r[3]]) + '</td><td>' + esc(D.tribes[r[4]]) + '</td><td class="st">' + esc(D.status[r[5]]) + '</td></tr>'; }).join('') + '</tbody></table>';
    }
    gq.addEventListener('input', function () {
      if (!loaded) { loaded = true; out.innerHTML = '<p>loading search index...</p>'; var s = document.createElement('script'); s.src = ROOT + 'Metadata/Browser/search_index.js'; s.onload = run; document.head.appendChild(s); return; }
      clearTimeout(timer); timer = setTimeout(run, 150);
    });
    function fromHash() { var h = location.hash.match(/q=([^&]*)/); if (h) { gq.value = decodeURIComponent(h[1]); if (loaded) run(); else gq.dispatchEvent(new Event('input')); } }
    window.addEventListener('hashchange', fromHash); fromHash();
  }
  document.addEventListener('DOMContentLoaded', function () {
    var c = document.getElementById('crumbs'); if (c) c.innerHTML = crumbs();
    var l = document.getElementById('list'); if (l) list(l);
    var s = document.getElementById('search'); if (s) search(s);
  });
})();
