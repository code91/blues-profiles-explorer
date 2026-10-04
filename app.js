/* Blues Profiles explorer. No dependencies, no build step.
   Everything is read from data/profiles.json, which build/export.py writes
   from the study's own analysis output. */
(function () {
  'use strict';

  var DATA = null, current = null, tab = 'vocab';
  var $ = function (id) { return document.getElementById(id); };

  function fmt(v, dp) {
    if (v === null || v === undefined || isNaN(v)) return 'n/a';
    return Number(v).toFixed(dp === undefined ? 2 : dp);
  }

  /* ---- radar -------------------------------------------------------- */
  // Room for the labels is the constraint, not the circle: the longest axis
  // name is wider than the radius, so the box is deliberately much wider
  // than tall and the outer labels sit at 1.16R.
  var CX = 230, CY = 165, R = 105, LABEL_R = 1.16;

  function point(i, n, frac) {
    var a = (Math.PI * 2 * i / n) - Math.PI / 2;
    return [CX + Math.cos(a) * R * frac, CY + Math.sin(a) * R * frac];
  }

  function drawRadar(artist) {
    var axes = artist.radar, n = axes.length, svg = $('radar'), parts = [];
    [0.25, 0.5, 0.75, 1].forEach(function (ring) {
      var pts = axes.map(function (_, i) { return point(i, n, ring).join(','); }).join(' ');
      parts.push('<polygon points="' + pts + '" fill="none" stroke="var(--border-color)" stroke-width="1"/>');
    });
    axes.forEach(function (_, i) {
      var p = point(i, n, 1);
      parts.push('<line x1="' + CX + '" y1="' + CY + '" x2="' + p[0] + '" y2="' + p[1] +
                 '" stroke="var(--border-color)" stroke-width="1"/>');
    });
    // the shape itself: a floor of 0.02 keeps a zero from vanishing into the hub
    var shape = axes.map(function (ax, i) {
      return point(i, n, Math.max(0.02, ax.norm)).join(',');
    }).join(' ');
    parts.push('<polygon points="' + shape + '" fill="var(--accent-light)" stroke="var(--accent)" ' +
               'stroke-width="2" stroke-linejoin="round"/>');
    axes.forEach(function (ax, i) {
      var p = point(i, n, Math.max(0.02, ax.norm));
      parts.push('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="3" fill="var(--accent)"/>');
    });
    axes.forEach(function (ax, i) {
      var p = point(i, n, LABEL_R), anchor = 'middle';
      if (p[0] > CX + 6) anchor = 'start';
      else if (p[0] < CX - 6) anchor = 'end';
      parts.push('<text x="' + p[0] + '" y="' + (p[1] + 4) + '" text-anchor="' + anchor +
                 '" font-size="11" fill="var(--text-secondary)">' + esc(ax.label) + '</text>');
    });
    svg.innerHTML = parts.join('');

    // Which of these axes the study could actually defend, stated where the
    // numbers are read rather than buried in a caption.
    var note = document.getElementById('profile-note');
    if (note && DATA && DATA.does_not_survive) {
      note.innerHTML = 'Of these six, only interval content distinguishes artists once baselines are ' +
        'applied. Blues quotient and interval entropy do not exceed what the chord changes alone produce, ' +
        'phrase length is indistinguishable from chance when solos rather than phrases are the unit, and ' +
        'vocabulary diversity reorders when every artist is sampled to the same number of phrases.';
    }

    $('axes-body').innerHTML = axes.map(function (ax) {
      var extra = '';
      if (ax.key === 'ttr' && artist.metrics && artist.metrics.ttr_rarefied != null) {
        // The raw ratio falls as a player contributes more phrases, so the value
        // at a common 29-phrase sample is the comparable one.
        extra = ' <span style="color:var(--text-muted)">(' +
                fmt(artist.metrics.ttr_rarefied, 2) + ' rarefied)</span>';
      }
      return '<tr><td>' + esc(ax.label) + '</td><td style="color:var(--text-secondary)">' +
             esc(ax.note) + '</td><td>' + fmt(ax.raw, ax.key === 'ttr' ? 3 : 2) + extra + '</td></tr>';
    }).join('');
  }

  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* ---- right-hand panel --------------------------------------------- */
  function faceOf(name) {
    var a = (DATA && DATA.artists || []).filter(function (x) { return x.name === name; })[0];
    return a && a.portrait ? a.portrait.img : null;
  }

  function bars(items, opts) {
    if (!items || !items.length) return '<p class="sub">No data for this artist.</p>';
    var vals = items.map(function (r) { return r.value; });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var span = hi - lo || 1;
    return '<div class="bars">' + items.map(function (r) {
      // a distance reads "closer = better", so invert the bar for those
      var t = opts.invert ? (hi - r.value) / span : (r.value - lo) / span;
      var pct = 12 + t * 88;
      var src = faceOf(r.name);
      var face = src ? '<img class="face-sm" src="' + esc(src) + '" alt="" width="28" height="28" loading="lazy">'
                     : '<span class="face-sm face-blank" aria-hidden="true"></span>';
      return '<div class="bar-row">' + face + '<span class="nm">' + esc(r.name) + '</span>' +
             '<span class="bar-track"><span class="bar-fill" style="width:' + pct.toFixed(1) + '%"></span></span>' +
             '<span class="v">' + fmt(r.value, 3) + '</span></div>';
    }).join('') + '</div>';
  }

  var PANELS = {
    vocab: {
      title: 'Closest vocabulary',
      sub: 'Jaccard overlap between the sets of interval vectors each artist uses. Higher is more alike. ' +
           'Interval vector distributions are the one artist-level difference that survives the study\u2019s baselines ' +
           '(eta squared 0.12, p = .003 permuting whole solos rather than phrases).',
      render: function (a) { return bars(a.similar_vocabulary, {}); }
    },
    traj: {
      title: 'Closest trajectory',
      exploratory: true,
      sub: 'Dynamic time warping distance between density trajectories across a solo. ' +
           'This is a distance, so lower is more alike, and the bars are drawn inverted to read the same way as the others. ' +
           'Exploratory: the trajectory analysis was dropped from the paper because the clustering was descriptive ' +
           'rather than testable. It is kept here because it is still a reasonable way to browse the corpus.',
      render: function (a) { return bars(a.similar_trajectory, { invert: true }); }
    },
    ivs: {
      title: 'Most frequent interval vectors',
      sub: 'The five this artist reaches for most often. This is frequency, not distinctiveness. ' +
           'Read the note count: a phrase touching 11 or 12 of the 12 pitch classes has almost ' +
           'only one possible vector, so a high count there reflects phrase length rather than a choice of sonority.',
      render: function (a) {
        if (!a.top_ivs.length) return '<p class="sub">No data for this artist.</p>';
        return '<ol class="ivs">' + a.top_ivs.map(function (r) {
          var saturated = r.notes && r.notes >= 10;
          return '<li><code>' + esc(r.iv) + '</code><div class="meta">' +
                 (r.notes ? r.notes + ' of 12 pitch classes' +
                   (saturated ? ' <span class="tag">near-chromatic</span>' : '') + ' · ' : '') +
                 r.count + ' phrases · ' + (r.proportion * 100).toFixed(1) +
                 '% of this artist’s phrases</div></li>';
        }).join('') + '</ol>';
      }
    },
    granger: {
      title: 'Phrase-to-phrase causality',
      sub: 'Does one quantity in a phrase predict another in the phrase that follows? ' +
           'PROACTIVE means the first leads the second; REACTIVE means it trails it. ' +
           'Gravity is the signed strength of the lead. NOTE: none of these relationships survives ' +
           'correction. Across 182 tests, thirteen reach p < .05 where roughly nine are expected from ' +
           'noise, and none survives false discovery rate correction at any lag from one to four. ' +
           'The paper reports this as a null result. Individual cells are shown for inspection, ' +
           'not as findings.',
      render: function (a) {
        var LABELS = {
          density_to_bluesiness: 'Density → blues vocabulary',
          dissonance_to_bluesiness: 'Dissonance ratio → blues vocabulary',
          entropy_to_bluesiness: 'Interval entropy → blues vocabulary',
          length_to_bluesiness: 'Phrase length → blues vocabulary',
          density_to_anticipation: 'Density → anticipation',
          length_to_density: 'Phrase length → density',
          density_to_dissonance: 'Density → dissonance ratio'
        };
        return '<div class="rel">' + Object.keys(LABELS).map(function (k) {
          var r = a.granger[k] || {}, dir = r.direction || 'NONE';
          var on = dir && dir !== 'NONE';
          return '<div class="rel-row' + (on ? ' sig' : '') + '">' +
                 '<div class="lab">' + esc(LABELS[k]) + ' <span class="tag' + (on ? ' on' : '') + '">' +
                 esc(dir) + '</span></div>' +
                 '<div class="val">gravity ' + fmt(r.gravity, 3) + '</div></div>';
        }).join('') + '</div>';
      }
    }
  };

  function renderPanel() {
    var p = PANELS[tab];
    $('panel-title').textContent = p.title;
    $('panel-sub').textContent = p.sub;
    $('panel').innerHTML = p.render(current);
  }

  function select(artist) {
    current = artist;
    $('artist-name').textContent = artist.name;
    var bits = [artist.instruments.join(', '),
                artist.solos + (artist.solos === 1 ? ' solo' : ' solos'),
                artist.phrases + ' phrases'];
    if (artist.style) bits.push(artist.style.toLowerCase());
    if (artist.anticipation_style) bits.push(artist.anticipation_style.toLowerCase() + ' phrasing');
    $('artist-meta').textContent = bits.join(' · ');
    Array.prototype.forEach.call($('picker').children, function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.name === artist.name));
    });

    var face = $('artist-face'), credit = $('photo-credit');
    if (artist.portrait && artist.portrait.img) {
      face.src = artist.portrait.img;
      face.alt = artist.name;
      face.hidden = false;
      // A CC photograph has to carry its author and terms wherever it appears.
      var who = artist.portrait.author ? artist.portrait.author : 'unknown photographer';
      credit.innerHTML = 'Portrait: ' + esc(who) + ', ' + esc(artist.portrait.licence || '') +
        (artist.portrait.source ? ' (<a href="' + esc(artist.portrait.source) +
          '" rel="noopener">Wikimedia Commons</a>)' : '');
    } else {
      face.hidden = true;
      face.removeAttribute('src');
      credit.textContent = '';
    }
    drawRadar(artist);
    renderPanel();
    try { localStorage.setItem('bp:artist', artist.name); } catch (e) { /* private mode */ }
  }

  /* ---- theme ---------------------------------------------------------
     Light is the default and the OS preference is deliberately not consulted:
     only an explicit choice here, remembered per browser. */
  function applyTheme(mode) {
    document.documentElement.setAttribute('data-theme', mode);
    var dark = mode === 'dark';
    var btn = $('theme');
    if (!btn) return;
    btn.setAttribute('aria-pressed', String(dark));
    $('theme-icon').textContent = dark ? '☀' : '☾';
    $('theme-label').textContent = dark ? 'Light' : 'Dark';
  }

  function initTheme() {
    var mode = 'light';
    try { if (localStorage.getItem('bp:theme') === 'dark') mode = 'dark'; } catch (e) { /* ignore */ }
    applyTheme(mode);
    var btn = $('theme');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('bp:theme', next); } catch (e) { /* ignore */ }
    });
  }

  function boot(d) {
    DATA = d;
    var c = d.corpus;
    $('corpus-line').textContent = c.solos + ' blues solos · ' + c.artists + ' artists · ' +
      c.phrases.toLocaleString() + ' phrases · ' + c.instruments.length + ' instruments · ' +
      'Weimar Jazz Database';
    $('picker').innerHTML = d.artists.map(function (a) {
      return '<button type="button" data-name="' + esc(a.name) + '" aria-pressed="false">' +
             esc(a.name) + '</button>';
    }).join('');
    $('picker').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-name]');
      if (!b) return;
      var a = d.artists.filter(function (x) { return x.name === b.dataset.name; })[0];
      if (a) select(a);
    });
    $('tabs').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-tab]');
      if (!b) return;
      tab = b.dataset.tab;
      Array.prototype.forEach.call($('tabs').children, function (x) {
        x.setAttribute('aria-pressed', String(x.dataset.tab === tab));
      });
      renderPanel();
    });

    var want = null;
    try { want = localStorage.getItem('bp:artist'); } catch (e) { /* ignore */ }
    var start = d.artists.filter(function (x) { return x.name === want; })[0] || d.artists[0];
    select(start);
  }

  initTheme();

  /* The data arrives as a global from data/profiles.js, loaded by a script tag.
     fetch() is only the fallback, because it cannot be relied on: a page served
     under a sandbox CSP without allow-same-origin has an opaque origin, where
     every fetch is cross-origin and blocked, and file:// behaves the same way. */
  if (window.BLUES_PROFILES) {
    boot(window.BLUES_PROFILES);
  } else {
    fetch('data/profiles.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(boot)
      .catch(function (err) {
        $('corpus-line').textContent = 'Could not load the profile data: ' + err.message;
      });
  }
})();
