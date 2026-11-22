"""FCHK Kurzy (cloudová verze, bez Macu) – feed 4:5 + stories 9:16.

python3 -I fchk_kurzy_cloud.py --bundle DIR --home Slovacko --away Hradec \
        --odds 3.01 3.51 2.34 --out DIR [--draft]
--home/--away = název loga v DIR/logos (Hradec, Slovacko, Sparta, Slavia, Plzeň, Baník,
Olomouc, Teplice, Liberec, Jablonec, Dukla, Pardubice, Karviná, Bohemians, Boleslav,
Zlin, Zrojovka, Artis). Kurzy v pořadí 1 / X / 2. Bez kurzů: --odds - - -  (vykreslí „–.––“).
"""
import argparse, base64, io, json, os
from PIL import Image

LABELS = {'Hradec': 'HRADEC', 'Hradec_výroční': 'HRADEC', 'Sparta': 'SPARTA', 'Slavia': 'SLAVIA',
          'Plzeň': 'PLZEŇ', 'Baník': 'BANÍK', 'Olomouc': 'OLOMOUC', 'Teplice': 'TEPLICE',
          'Liberec': 'LIBEREC', 'Jablonec': 'JABLONEC', 'Dukla': 'DUKLA', 'Pardubice': 'PARDUBICE',
          'Karviná': 'KARVINÁ', 'Bohemians': 'BOHEMIANS', 'Boleslav': 'BOLESLAV',
          'Slovacko': 'SLOVÁCKO', 'Zlin': 'ZLÍN', 'Zrojovka': 'ZBROJOVKA', 'Artis': 'ARTIS'}

ap = argparse.ArgumentParser()
ap.add_argument('--bundle', required=True)
ap.add_argument('--home', required=True)
ap.add_argument('--away', required=True)
ap.add_argument('--odds', nargs=3, required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--draft', action='store_true')
a = ap.parse_args()
B = lambda *p: os.path.join(a.bundle, *p)
os.makedirs(a.out, exist_ok=True)


def load_font(key):
    g = json.load(open(B(f'glyphs_{key}.json')))
    for v in g.values():
        if 'png' in v:
            v['img'] = Image.open(io.BytesIO(base64.b64decode(v['png']))).convert('L')
    return g


NUM, LBL = load_font('num'), load_font('lbl')


def text_center(canvas, cx, base, s, font, color):
    w = sum(font[c]['adv'] for c in s)
    x = cx - w / 2
    for c in s:
        g = font[c]
        if 'img' in g:
            layer = Image.new('RGBA', g['img'].size, color)
            canvas.paste(layer, (round(x + g['x']), round(base + g['y'])), g['img'])
        x += g['adv']


def logo(name):
    p = B('logos', name + '.png')
    if not os.path.exists(p):
        raise SystemExit(f'Logo „{name}“ chybí. K dispozici: ' +
                         ', '.join(sorted(f[:-4] for f in os.listdir(B('logos')))))
    return Image.open(p).convert('RGBA')


def fit(img, size):
    s = size / max(img.size)
    return img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)


odds = ['–.––' if o in ('-', '') else o for o in a.odds]
labels = [LABELS.get(a.home, a.home.upper()), 'REMÍZA', LABELS.get(a.away, a.away.upper())]
X = Image.open(B('x.png')).convert('RGBA')
WHITE, YELLOW = (255, 255, 255, 255), (255, 237, 0, 255)
COLS, NUM_BASE, LBL_BASE = [244, 545, 865], 936, 1007

opp = a.away if a.home.startswith('Hradec') else a.home
for fmt, size, (dx, dy) in (('feed', '1080x1350', (0, 0)), ('stories', '1080x1920', (-20, 152))):
    c = Image.open(B(f'bg_{fmt}.jpg')).convert('RGBA')
    for (x, y, s), lg in (((106, 434, 265), logo(a.home)), ((735, 434, 260), logo(a.away))):
        l = fit(lg, s)
        c.alpha_composite(l, (x + dx + (s - l.width) // 2, y + dy + (s - l.height) // 2))
    c.alpha_composite(X, (436 + dx, 462 + dy))
    for cx, o, t in zip(COLS, odds, labels):
        text_center(c, cx + dx, NUM_BASE + dy, o, NUM, WHITE)
        text_center(c, cx + dx, LBL_BASE + dy, t, LBL, YELLOW)
    fn = os.path.join(a.out, f'FCHK_kurzy_{opp}{"_NAHLED" if a.draft else ""}_{fmt}_{size}.png')
    c.convert('RGB').save(fn, optimize=True)
    print(fn)
