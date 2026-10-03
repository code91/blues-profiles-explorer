# Blues Profiles — explorer

An interactive view of cross-artist profiles of improvisational decision-making on blues
form: 48 solos by 13 artists (1,170 phrases) drawn from the
[Weimar Jazz Database](https://jazzomat.hfm-weimar.de), restricted to blues.

**Live:** https://code91.github.io/blues-profiles-explorer/

Companion to the analysis pipeline in
[blues-profiles](https://github.com/code91/blues-profiles).

## What it shows

- **Profile** — a radar over six measures: vocabulary diversity (type–token ratio), blues
  quotient, blues breadth, phrase length, harmonic density and anticipation balance. Axes are
  min–max normalised *across the thirteen artists*, so a point means "relative to the others in
  this corpus", never an absolute score. The raw value is always printed beneath.
- **Closest vocabulary** — Jaccard overlap between the sets of interval vectors each artist
  uses. Higher is more alike.
- **Closest trajectory** — dynamic time warping distance between complexity trajectories over a
  solo. This is a *distance*, so lower is more alike; the bars are drawn inverted so they read
  the same direction as the others.
- **Frequent intervals** — the five interval vectors each artist uses most, with the number of
  pitch classes each implies.
- **Causality** — whether one quantity in a phrase predicts another in the phrase that follows,
  as a direction (proactive / reactive / none) and a signed gravity.

## A caveat worth reading

The "Frequent intervals" panel reports **frequency, not distinctiveness**, and the two are not
the same thing here. An interval vector is determined by the pitch-class set of a phrase, and a
phrase touching 11 or 12 of the 12 pitch classes has almost only one possible vector — so a
high count on a near-chromatic vector reflects how long an artist's phrases run, not a choice of
sonority. The panel prints the implied set size next to every vector for that reason, and
flags the near-chromatic ones. A genuine distinctiveness measure (lift against the corpus-wide
distribution) is not yet computed.

## How it is built

No framework, no build step, no runtime dependencies — a static page, a stylesheet and one
script, reading a single JSON file. `build/export.py` flattens the analysis outputs of scripts
01–09 in the companion repository into `data/profiles.json`:

```bash
python3 build/export.py /path/to/blues-profiles > data/profiles.json
```

Nothing is computed in the browser and nothing is computed in the export that the study did not
already compute, with one exception: the min–max normalisation behind the radar, which is
carried alongside the raw value so both are visible.

## Data and licence

Source transcriptions are from the Weimar Jazz Database, provided under academic use terms by
the Jazzomat Research Project at the Hochschule für Musik Franz Liszt Weimar. No audio is
distributed here. Derived figures and code in this repository follow the companion repository's
terms, CC BY-NC-SA 4.0.
