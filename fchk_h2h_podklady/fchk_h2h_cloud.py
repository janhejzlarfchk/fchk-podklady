"""FCHK Head2Head (cloudová verze) – feed 1080×1350 + stories 1080×1920.

python3 -I fchk_h2h_cloud.py --bundle DIR --home Slovacko --away Hradec \
    --home-stats 15 2 13 26 10 --away-stats 11 1 17 18 18 --out DIR
Statistiky v pořadí: pozice, výhry z posledních 5 ligových zápasů, vstřelené góly,
obdržené góly, body (vše jen Chance Liga). Domácí tým je vždy vlevo.
--home/--away = název loga v DIR/logos bez .png (Hradec, Slovacko, Sparta, Slavia, Plzeň,
Baník, Olomouc, Teplice, Liberec, Jablonec, Dukla, Pardubice, Karviná, Bohemians, Boleslav,
Zlin, Zrojovka, Artis, Hradec_výroční).
"""
import argparse, base64, io, json, os
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--bundle', required=True)
ap.add_argument('--home', required=True)
ap.add_argument('--away', required=True)
ap.add_argument('--home-stats', nargs=5, required=True)
ap.add_argument('--away-stats', nargs=5, required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--tag', default='')
a = ap.parse_args()
B = lambda *p: os.path.join(a.bundle, *p)
os.makedirs(a.out, exist_ok=True)
cfg = json.load(open(B('cfg.json')))
GL = json.load(open(B('glyphs_num.json')))
for f in GL.values():
    for g in f['g'].values():
        g['img'] = Image.open(io.BytesIO(base64.b64decode(g['png']))).convert('L')
YELLOW = (255, 237, 0, 255)


def logo(name):
    p = B('logos', name + '.png')
    if not os.path.exists(p):
        raise SystemExit(f'Logo „{name}“ chybí. K dispozici: ' +
                         ', '.join(sorted(f[:-4] for f in os.listdir(B('logos')))))
    return Image.open(p).convert('RGBA')


def draw_num(c, s, cx, top, font):
    s = str(s)
    for ch in s:
        if ch not in font['g']:
            raise SystemExit(f'Znak „{ch}“ v číslech není podporovaný: {s}')
    w = sum(font['g'][ch]['adv'] for ch in s)
    # center on ink bbox for accuracy
    x0 = cx - w / 2
    ink_l = x0 + font['g'][s[0]]['x']
    last = font['g'][s[-1]]
    ink_r = x0 + w - last['adv'] + last['x'] + last['img'].width
    x = x0 + (cx - (ink_l + ink_r) / 2)
    for ch in s:
        g = font['g'][ch]
        layer = Image.new('RGBA', g['img'].size, YELLOW)
        c.paste(layer, (round(x + g['x']), round(top - font['capTop'] + g['y'])), g['img'])
        x += g['adv']


opp = a.away if a.home.startswith('Hradec') else a.home
for fmt, (W, H) in (('feed', (1080, 1350)), ('stories', (1080, 1920))):
    k = cfg[fmt]
    c = Image.open(B(f'base_{fmt}.jpg')).convert('RGBA')
    for (x0, y0, x1, y1), name in zip(k['slots'], (a.home, a.away)):
        sw, sh = x1 - x0, y1 - y0
        lg = logo(name)
        s = min(sw / lg.width, sh / lg.height)
        l = lg.resize((round(lg.width * s), round(lg.height * s)), Image.LANCZOS)
        c.alpha_composite(l, (round(x0 + (sw - l.width) / 2), round(y0 + (sh - l.height) / 2)))
    font = GL[fmt]
    for side, vals in (('L', a.home_stats), ('R', a.away_stats)):
        for row, v in zip(k['cols'][side], vals):
            cx = sum(r['cx'] for r in k['cols'][side]) / 5
            draw_num(c, v, cx, row['top'], font)
    c = c.crop((0, 0, W, H))
    fn = os.path.join(a.out, f'FCHK_H2H_{opp}{a.tag}_{fmt}_{W}x{H}.png')
    c.convert('RGB').save(fn, optimize=True)
    print(fn)
