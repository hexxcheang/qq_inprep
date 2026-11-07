# Trace the EPTC 2026 logo (raster) into a clean vector SVG with three layers:
# EPTC letters (vertical gradient), 2026 digits (dark red gradient), circuit traces (orange).
import sys, numpy as np, cv2, potrace
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
a = np.array(Image.open(src).convert('RGB')).astype(float)
H, W = a.shape[:2]
R, G, B = a[..., 0], a[..., 1], a[..., 2]
hard = ((R - B) > 45) | ((R + G + B) < 560)
n, lab, st, _ = cv2.connectedComponentsWithStats(hard.astype(np.uint8), 8)
groups = {'letters': [], 'digits': [], 'traces': []}
for i in range(1, n):
    x, y, w, h, ar = st[i]
    if ar < 15: continue
    if h > 90: groups['letters'].append(i)
    elif x > 420 and y > 145: groups['digits'].append(i)
    else: groups['traces'].append(i)
soft = np.clip((254 - B) / (254 - 15), 0, 1)          # anti-aliased coverage
S = 8
def trace(ids):
    region = cv2.dilate(np.isin(lab, ids).astype(np.uint8), np.ones((5, 5), np.uint8))
    m = soft * region
    big = cv2.resize(m, (W * S, H * S), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), S * 0.35)
    bm = potrace.Bitmap(~(big > 0.5))  # potracer treats False as ink
    pl = bm.trace(turdsize=20, alphamax=0.8, opticurve=True, opttolerance=0.15)
    f = lambda p: f'{p.x / S:.2f} {p.y / S:.2f}'
    d = []
    for c in pl:
        d.append('M' + f(c.start_point))
        for sgm in c.segments:
            if sgm.is_corner: d.append('L' + f(sgm.c) + ' L' + f(sgm.end_point))
            else: d.append('C' + f(sgm.c1) + ' ' + f(sgm.c2) + ' ' + f(sgm.end_point))
        d.append('Z')
    return ' '.join(d)
def grad(ids, gid, y0, y1, k=5):
    m = np.isin(lab, ids) & (soft > 0.97)
    stops = []
    for t in np.linspace(0, 1, k):
        y = int(round(y0 + t * (y1 - y0)))
        band = m[max(y - 2, 0):y + 3]
        cols = a[max(y - 2, 0):y + 3][band]
        if len(cols): stops.append((t, cols.mean(0)))
    s = ''.join(f'<stop offset="{t:.2f}" stop-color="#{int(c[0]):02X}{int(c[1]):02X}{int(c[2]):02X}"/>' for t, c in stops)
    return f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y0}" x2="0" y2="{y1}">{s}</linearGradient>'
def bbox(ids):
    xs = [st[i][0] for i in ids]; ys = [st[i][1] for i in ids]
    xe = [st[i][0] + st[i][2] for i in ids]; ye = [st[i][1] + st[i][3] for i in ids]
    return min(xs), min(ys), max(xe), max(ye)
L, D, T = groups['letters'], groups['digits'], groups['traces']
_, ly0, _, ly1 = bbox(L); _, dy0, _, dy1 = bbox(D); tx0, ty0, tx1, ty1 = bbox(T)
allx0, ally0, allx1, ally1 = bbox(L + D + T)
pad = 2
vb = f'{allx0 - pad} {ally0 - pad} {allx1 - allx0 + 2 * pad} {ally1 - ally0 + 2 * pad}'
tm = np.isin(lab, T) & (soft > 0.97); tc = a[tm].mean(0)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">
<defs>{grad(L, "eptcL", ly0, ly1)}{grad(D, "eptcD", dy0, dy1, 3)}</defs>
<path fill="url(#eptcL)" fill-rule="evenodd" d="{trace(L)}"/>
<path fill="url(#eptcD)" fill-rule="evenodd" d="{trace(D)}"/>
<path fill="#{int(tc[0]):02X}{int(tc[1]):02X}{int(tc[2]):02X}" fill-rule="evenodd" d="{trace(T)}"/>
</svg>'''
open(out, 'w').write(svg)
print('viewBox', vb, 'groups', {k: len(v) for k, v in groups.items()})
