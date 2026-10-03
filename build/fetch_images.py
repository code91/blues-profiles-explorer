#!/usr/bin/env python3
"""
Fetch one freely-licensed portrait per artist from Wikimedia Commons, square
them all to the same size, and write img/credits.json alongside.

    python3 build/fetch_images.py

Only public-domain, CC0, CC BY and CC BY-SA files are accepted; anything else
is refused rather than downloaded, because these are photographs of real people
and the page is public. Every file keeps its author and licence in
img/credits.json, which the page renders as a caption.

The crop is square and centred horizontally, but sits high vertically: in a
portrait the face is usually in the upper third, and a dead-centre square
decapitates people often enough to be worth the asymmetry.
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

from PIL import Image

UA = {'User-Agent': 'blues-profiles-explorer/1.0 (academic research)'}
SIZE = 320
TOP_BIAS = 0.38           # where the crop's centre sits, as a fraction of height
OUT = os.path.join(os.path.dirname(__file__), '..', 'img')

OK_LICENCES = ('public domain', 'cc0', 'cc by')   # CC BY-SA starts with "cc by"

# Wikipedia's lead image, except where it has none and the file is named by hand.
ARTISTS = {
    "Branford Marsalis": None, "Charlie Parker": None, "Don Byas": None,
    "Eric Dolphy": "Eric Dolphy - uncredited photo in The Jazz Review - June 1960 issue.jpg",
    "Freddie Hubbard": None, "J. J. Johnson": None, "John Coltrane": None,
    "Kenny Dorham": None, "Louis Armstrong": None, "Miles Davis": None,
    "Sonny Rollins": None, "Steve Coleman (musician)": "Steve Coleman 1611.JPG",
    "Wayne Shorter": None,
}
# How the artist is named in the analysis data, where it differs from Wikipedia.
AS_IN_DATA = {"J. J. Johnson": "J.J. Johnson", "Steve Coleman (musician)": "Steve Coleman"}


def api(host, params):
    u = 'https://%s/w/api.php?%s' % (host, urllib.parse.urlencode(params))
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 5:
                raise
            time.sleep(10 * (i + 1))
    return {}


def lead_file(title):
    d = api('en.wikipedia.org', {'action': 'query', 'format': 'json', 'titles': title,
                                 'prop': 'pageimages', 'piprop': 'name'})
    for p in (d.get('query', {}).get('pages') or {}).values():
        if p.get('pageimage'):
            return p['pageimage']
    return None


def file_info(fname):
    d = api('commons.wikimedia.org', {'action': 'query', 'format': 'json',
                                      'titles': 'File:' + fname, 'prop': 'imageinfo',
                                      'iiprop': 'url|extmetadata|size', 'iiurlwidth': 900})
    for p in (d.get('query', {}).get('pages') or {}).values():
        ii = (p.get('imageinfo') or [{}])[0]
        if not ii:
            return None
        md = ii.get('extmetadata') or {}
        g = lambda k: re.sub(r'<[^>]+>', '', (md.get(k) or {}).get('value') or '').strip()
        return {'file': fname, 'licence': g('LicenseShortName'), 'author': g('Artist'),
                'url': ii.get('thumburl') or ii.get('url'), 'descurl': ii.get('descriptionurl')}
    return None


def square(raw):
    im = Image.open(io.BytesIO(raw))
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = int(h * TOP_BIAS - side / 2)
    top = max(0, min(top, h - side))
    im = im.crop((left, top, left + side, top + side))
    return im.resize((SIZE, SIZE), Image.LANCZOS).convert('RGB')


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def main():
    os.makedirs(OUT, exist_ok=True)
    credits = {}
    for title, manual in ARTISTS.items():
        who = AS_IN_DATA.get(title, title)
        fname = manual or lead_file(title)
        if not fname:
            print('  %-22s no image found' % who); continue
        time.sleep(1.5)
        info = file_info(fname)
        if not info:
            print('  %-22s no Commons record' % who); continue
        lic = (info['licence'] or '').lower()
        if not any(lic.startswith(ok) or ok in lic for ok in OK_LICENCES):
            print('  %-22s REFUSED, licence %r' % (who, info['licence'])); continue
        raw = urllib.request.urlopen(
            urllib.request.Request(info['url'], headers=UA), timeout=60).read()
        name = slug(who) + '.jpg'
        square(raw).save(os.path.join(OUT, name), 'JPEG', quality=86, optimize=True)
        credits[who] = {'img': 'img/' + name, 'licence': info['licence'],
                        'author': re.sub(r'\s+', ' ', info['author'])[:120],
                        'source': info['descurl']}
        print('  %-22s %-15s %s' % (who, info['licence'], name))
        time.sleep(2)
    with open(os.path.join(OUT, 'credits.json'), 'w', encoding='utf-8') as fh:
        json.dump(credits, fh, indent=1, ensure_ascii=False)
    print('\n%d portraits, credits written' % len(credits))


if __name__ == '__main__':
    main()
