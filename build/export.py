#!/usr/bin/env python3
"""
Flatten the blues-profiles analysis outputs into one JSON the static explorer
reads. Run it against a checkout of the analysis repo:

    python3 build/export.py /path/to/paper-blues-profiles data

Everything here is a projection of files already produced by scripts 01-09.
Nothing is computed that the study did not compute; the only new work is
min-max normalisation for the radar, which is carried alongside the raw value
so the page can always show both.
"""
import csv, json, math, os, sys
from collections import defaultdict

root = sys.argv[1] if len(sys.argv) > 1 else '.'
A = os.path.join(root, 'data', 'analysis')


def rows(path):
    with open(path, newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def load(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


INSTRUMENTS = {'ts': 'tenor saxophone', 'as': 'alto saxophone', 'tp': 'trumpet',
               'tb': 'trombone', 'cor': 'cornet', 'bcl': 'bass clarinet',
               'ss': 'soprano saxophone', 'bs': 'baritone saxophone',
               'cl': 'clarinet', 'fl': 'flute', 'g': 'guitar', 'p': 'piano'}

meta = rows(os.path.join(root, 'data', 'corpus_metadata.csv'))
vocab = {r['performer']: r for r in rows(os.path.join(A, 'vocabulary_by_artist.csv'))}
granger = {r['performer']: r for r in rows(os.path.join(A, 'granger_results.csv'))}
blues = {a['performer']: a for a in load(os.path.join(A, 'blues_stats.json'))['artists']}
antic = {a['performer']: a for a in load(os.path.join(A, 'anticipation_stats.json'))['artist_profiles']}
clusters = load(os.path.join(A, 'cluster_analysis.json'))

# Phrase-level series, averaged per artist. Entropy is the complexity measure
# the IV sum is not; density is that sum, named for what it measures.
series = defaultdict(lambda: defaultdict(list))
for r in rows(os.path.join(root, 'data', 'timeseries', 'timeseries_data.csv')):
    for col in ('density', 'entropy', 'dissonance_ratio'):
        v = num(r.get(col))
        if v is not None:
            series[r['performer']][col].append(v)


def mean_of(name, col):
    vals = series.get(name, {}).get(col) or []
    return sum(vals) / len(vals) if vals else None
dtw = load(os.path.join(A, 'dtw_results.json'))

# Portraits, if build/fetch_images.py has been run. Every entry carries its
# author and licence, which the page is obliged to show: these are real
# photographs under CC terms, not decoration.
credits_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'img', 'credits.json')
portraits = load(credits_path) if os.path.exists(credits_path) else {}

# solos, instruments and recording years, straight off the corpus sheet
solos = defaultdict(list)
for r in meta:
    solos[r['performer']].append(r)

def set_size(iv):
    """How many pitch classes an interval vector implies.

    An n-note set has C(n,2) intervals, so the sum of the vector determines n.
    Worth carrying, because a near-chromatic phrase has essentially only one
    possible IV: raw IV frequency partly measures phrase length rather than
    choice, and the page says so rather than calling it distinctiveness.
    """
    total = sum(int(x) for x in iv.strip('[]').split(','))
    n = (1 + math.isqrt(1 + 8 * total)) // 2
    return n if n * (n - 1) // 2 == total else None


top_ivs = defaultdict(list)
for r in rows(os.path.join(A, 'top_ivs_by_artist.csv')):
    top_ivs[r['performer']].append({
        'rank': int(r['rank']), 'iv': r['iv'],
        'count': int(r['count']), 'proportion': num(r['proportion']),
        'notes': set_size(r['iv']),
    })

# Jaccard: vocabulary overlap, 1.0 on the diagonal
jac_rows = rows(os.path.join(A, 'jaccard_similarity_matrix.csv'))
jac_key = jac_rows[0] and list(jac_rows[0])[0]
jaccard = {}
for r in jac_rows:
    src = r[jac_key]
    jaccard[src] = {k: num(v) for k, v in r.items()
                    if k != jac_key and k != src and num(v) is not None}

# DTW over complexity trajectories: a DISTANCE, 0.0 on the diagonal
dtw_names = dtw['performers']
dtw_dist = {}
for i, a in enumerate(dtw_names):
    dtw_dist[a] = {b: dtw['dtw_density_matrix'][i][j]
                   for j, b in enumerate(dtw_names) if b != a}

artists = []
for name in sorted(vocab):
    v, g = vocab[name], granger.get(name, {})
    b, an = blues.get(name, {}), antic.get(name, {})
    mine = solos.get(name, [])
    insts = sorted({INSTRUMENTS.get(s['instrument'], s['instrument']) for s in mine})
    artists.append({
        'name': name,
        'instruments': insts,
        'solos': len(mine),
        'phrases': int(v['total_phrases']),
        'style': clusters.get('style_labels', {}).get(name),
        'cluster': clusters.get('cluster_assignments', {}).get('k=3', {}).get(name),
        'metrics': {
            'ttr': num(v['type_token_ratio']),
            'unique_ivs': num(v['unique_ivs']),
            'phrase_length': num(v['mean_phrase_length']),
            'cardinality': num(v['mean_cardinality']),
            'density': mean_of(name, 'density'),
            'entropy': mean_of(name, 'entropy'),
            'dissonance_ratio': mean_of(name, 'dissonance_ratio'),
            'blues_quotient': num(b.get('blues_quotient')),
            'blues_breadth': num(b.get('blues_vocabulary_breadth')),
            'blues_commitment': num(b.get('blues_commitment_normalized')),
            'loading_balance': num(an.get('loading_balance_mean')),
            'convergence': num(an.get('convergence_speed_mean')),
        },
        'anticipation_style': an.get('style'),
        'granger': {
            'density_to_dissonance': {'direction': g.get('cd_direction'), 'gravity': num(g.get('cd_gravity'))},
            'density_to_anticipation': {'direction': g.get('ca_direction'), 'gravity': num(g.get('ca_gravity'))},
            'length_to_density': {'direction': g.get('lc_direction'), 'gravity': num(g.get('lc_gravity'))},
            'density_to_bluesiness': {'direction': g.get('cb_direction'), 'gravity': num(g.get('cb_gravity'))},
            'entropy_to_bluesiness': {'direction': g.get('eb_direction'), 'gravity': num(g.get('eb_gravity'))},
            'dissonance_to_bluesiness': {'direction': g.get('db_direction'), 'gravity': num(g.get('db_gravity'))},
            'length_to_bluesiness': {'direction': g.get('lb_direction'), 'gravity': num(g.get('lb_gravity'))},
        },
        'portrait': portraits.get(name),
        'top_ivs': sorted(top_ivs.get(name, []), key=lambda r: r['rank'])[:5],
        'similar_vocabulary': sorted(
            ({'name': k, 'value': val} for k, val in jaccard.get(name, {}).items()),
            key=lambda r: -r['value'])[:5],
        'similar_trajectory': sorted(
            ({'name': k, 'value': val} for k, val in dtw_dist.get(name, {}).items()),
            key=lambda r: r['value'])[:5],
    })

# Min-max across the thirteen, so a radar point means "relative to this corpus"
RADAR = [
    ('ttr',            'Vocabulary diversity', 'type-token ratio'),
    ('blues_quotient', 'Blues quotient',       '% of phrases using canonical blues IVs'),
    ('blues_breadth',  'Blues breadth',        'distinct blues IVs deployed'),
    ('phrase_length',  'Phrase length',        'mean notes per phrase'),
    ('entropy',        'Interval entropy',     'evenness of interval content, in bits'),
    ('loading_balance','Anticipation',         'front-loaded (+) vs back-loaded (-)'),
]
bounds = {}
for key, _, _ in RADAR:
    vals = [a['metrics'][key] for a in artists if a['metrics'].get(key) is not None]
    bounds[key] = {'min': min(vals), 'max': max(vals)} if vals else {'min': 0, 'max': 1}

for a in artists:
    a['radar'] = []
    for key, label, note in RADAR:
        raw = a['metrics'].get(key)
        lo, hi = bounds[key]['min'], bounds[key]['max']
        norm = 0.0 if raw is None or hi == lo else (raw - lo) / (hi - lo)
        a['radar'].append({'key': key, 'label': label, 'note': note,
                           'raw': raw, 'norm': round(norm, 4)})

out = {
    'generated_from': 'blues-profiles analysis outputs (scripts 01-09)',
    'corpus': {
        'solos': len(meta),
        'artists': len(artists),
        'phrases': sum(a['phrases'] for a in artists),
        'instruments': sorted({INSTRUMENTS.get(r['instrument'], r['instrument']) for r in meta}),
    },
    'radar_axes': [{'key': k, 'label': l, 'note': n} for k, l, n in RADAR],
    'bounds': bounds,
    'artists': artists,
}
blob = json.dumps(out, indent=1, ensure_ascii=False)

# Two copies of the same thing, on purpose.
#
# profiles.json is the raw data, for anyone who wants it. profiles.js assigns
# the same object to a global and is what the page actually reads, because a
# script tag is not subject to CORS and fetch() is. Anonymous GitHub serves
# every file under "content-security-policy: sandbox allow-scripts", with no
# allow-same-origin, which drops the page into an opaque origin: there, every
# fetch is cross-origin and fails, even for a file sitting next to the page.
# The same applies to opening the page straight off disk with file://.
dest = sys.argv[2] if len(sys.argv) > 2 else None
if dest:
    with open(os.path.join(dest, 'profiles.json'), 'w', encoding='utf-8') as fh:
        fh.write(blob + '\n')
    with open(os.path.join(dest, 'profiles.js'), 'w', encoding='utf-8') as fh:
        fh.write('/* Generated by build/export.py. Do not edit. */\n'
                 'window.BLUES_PROFILES = ' + blob + ';\n')
    sys.stderr.write('wrote profiles.json and profiles.js to %s\n' % dest)
else:
    sys.stdout.write(blob + '\n')
