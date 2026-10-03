# Blues Profiles explorer

An interactive view of cross-artist profiles of improvisational decision-making on blues
form: 48 solos by 13 artists (1,170 phrases) drawn from the
[Weimar Jazz Database](https://jazzomat.hfm-weimar.de), restricted to blues.

**Live:** https://code91.github.io/blues-profiles-explorer/

Companion to the analysis pipeline in
[blues-profiles](https://github.com/code91/blues-profiles).

## What it shows

- **Profile**: a radar over six measures: vocabulary diversity (type-token ratio), blues
  quotient, blues breadth, phrase length, interval entropy and anticipation balance. Axes are
  min-max normalised *across the thirteen artists*, so a point means "relative to the others in
  this corpus", never an absolute score. The raw value is always printed beneath.
- **Closest vocabulary**: Jaccard overlap between the sets of interval vectors each artist
  uses. Higher is more alike.
- **Closest trajectory**: dynamic time warping distance between complexity trajectories over a
  solo. This is a *distance*, so lower is more alike; the bars are drawn inverted so they read
  the same direction as the others.
- **Frequent intervals**: the five interval vectors each artist uses most, with the number of
  pitch classes each implies.
- **Causality**: whether one quantity in a phrase predicts another in the phrase that follows,
  as a direction (proactive / reactive / none) and a signed gravity. Note that *density* is the
  sum of the interval vector, which equals C(n,2) in the number of distinct pitch classes and so
  measures how many notes a phrase uses, not how complex it is. Interval entropy is the measure
  that is not reducible to set size. Dissonance is reported as a ratio to density, because the
  raw figures correlate at r = 0.99 by construction.

## A caveat worth reading

The "Frequent intervals" panel reports **frequency, not distinctiveness**, and the two are not
the same thing here. An interval vector is determined by the pitch-class set of a phrase, and a
phrase touching 11 or 12 of the 12 pitch classes has almost only one possible vector, so a
high count on a near-chromatic vector reflects how long an artist's phrases run, not a choice of
sonority. The panel prints the implied set size next to every vector for that reason, and
flags the near-chromatic ones. A genuine distinctiveness measure (lift against the corpus-wide
distribution) is not yet computed.

## Portraits

One photograph per artist, all squared to 320x320. `build/fetch_images.py` takes each artist's
lead image from Wikipedia, checks its licence on Wikimedia Commons, and **refuses anything that
is not public domain, CC0, CC BY or CC BY-SA** rather than downloading it. The current set is
eight public domain, one CC0, two CC BY and two CC BY-SA. Author, licence and source URL are
stored in `img/credits.json` and shown under every portrait, because these are photographs of
real people under terms that require it.

The crop is square and centred horizontally but sits high vertically, at 38% of the height: in
a portrait the face is usually in the upper third, and a dead-centre square decapitates people
often enough to be worth the asymmetry.

```bash
python3 build/fetch_images.py
```

## How it is built

No framework, no build step, no runtime dependencies: a static page, a stylesheet and one
script. `build/export.py` flattens the analysis outputs of scripts 01-09 in the companion
repository, folding in the portrait credits:

```bash
python3 build/export.py /path/to/blues-profiles data
```

That writes two files. `data/profiles.json` is the raw data for anyone who wants it;
`data/profiles.js` assigns the same object to a global and is what the page actually reads.

The duplication is deliberate. A script tag is not subject to CORS and `fetch` is, and the page
has to survive being served from an opaque origin: Anonymous GitHub sends every file under
`content-security-policy: sandbox allow-scripts` with no `allow-same-origin`, which makes every
fetch cross-origin and fails it, even for a file sitting next to the page. Opening the page
straight off disk with `file://` has the same problem. `fetch` is kept as a fallback.

Nothing is computed in the browser and nothing is computed in the export that the study did not
already compute, with one exception: the min-max normalisation behind the radar, which is
carried alongside the raw value so both are visible.

## Data and licence

Source transcriptions are from the Weimar Jazz Database, provided under academic use terms by
the Jazzomat Research Project at the Hochschule für Musik Franz Liszt Weimar. No audio is
distributed here. Portraits are individually licensed, each credited in `img/credits.json` and
on the page. Derived figures and code in this repository follow the companion repository's
terms, CC BY-NC-SA 4.0.
