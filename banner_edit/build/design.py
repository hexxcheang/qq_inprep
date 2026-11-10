import pymupdf, numpy as np, math, random
from PIL import Image, ImageFilter, ImageDraw
random.seed(7); rng = np.random.default_rng(7)
dist = np.load('v2/dist.npy'); H, W = dist.shape
YMAX = 1255                                  # never draw into the reg-table / skyline band
dist[YMAX:] = 0
# fade y in the last 60pt above the band
fade_y = np.clip((YMAX - np.arange(H))/60.0, 0, 1)[:, None]
clear = dist*fade_y
def C(x, y):
    xi, yi = int(round(x)), int(round(y))
    if xi < 0 or yi < 0 or xi >= W or yi >= H: return 0.0 if (yi >= YMAX or yi < 88) else 999.0
    return float(clear[yi, xi])
CL0, CL1 = 22, 90                            # clearance where art starts / reaches full strength
def alpha_at(x, y): return max(0.0, min(1.0, (C(x, y)-CL0)/(CL1-CL0)))

RUST = (0.663, 0.125, 0.0); ORANGE = (0.91, 0.39, 0.11); AMBER = (0.96, 0.60, 0.25); SOFT = (0.93, 0.55, 0.42)
doc = pymupdf.open(); pg = doc.new_page(width=W, height=H)
glow = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(glow)
nodes = []

# ---------------- wafer in the empty Media Partners column ----------------
def wafer(cx, cy, r, pitch, op):
    sh = pg.new_shape()
    sh.draw_circle((cx, cy), r); sh.finish(color=RUST, width=2.2, stroke_opacity=op)
    sh.draw_circle((cx, cy), r-8); sh.finish(color=ORANGE, width=0.8, stroke_opacity=op*0.8, dashes='[3 4] 0')
    # notch
    sh.draw_circle((cx, cy+r), 7); sh.finish(color=(1, 1, 1), fill=(1, 1, 1), width=0)
    n = int(r//pitch)+1
    for i in range(-n, n+1):
        for j in range(-n, n+1):
            x0, y0 = cx+i*pitch-pitch/2, cy+j*pitch-pitch/2
            corners = [(x0, y0), (x0+pitch, y0), (x0, y0+pitch), (x0+pitch, y0+pitch)]
            if all(math.hypot(px-cx, py-cy) < r-12 for px, py in corners):
                a = op*min(1, alpha_at(x0+pitch/2, y0+pitch/2)*1.5)
                if a <= 0.02: continue
                hot = random.random() < 0.10
                sh.draw_rect(pymupdf.Rect(x0+1.5, y0+1.5, x0+pitch-1.5, y0+pitch-1.5))
                sh.finish(color=ORANGE if hot else RUST, fill=AMBER if hot else None, width=0.7,
                          stroke_opacity=a*0.9, fill_opacity=a*0.45)
                if hot: nodes.append((x0+pitch/2, y0+pitch/2, 10, a))
    sh.commit()
wafer(2582, 1085, 150, 24, 0.55)
_yy, _xx = np.ogrid[0:H, 0:W]
clear[(_xx-2582)**2 + (_yy-1085)**2 < (150+28)**2] = 0      # keep traces off the wafer

# ---------------- chips (QFN/QFP style) at roomy spots ----------------
def chip(cx, cy, s, op, rot45=False):
    sh = pg.new_shape()
    r = pymupdf.Rect(cx-s/2, cy-s/2, cx+s/2, cy+s/2)
    sh.draw_rect(r, radius=0.08); sh.finish(color=RUST, fill=(1, 0.97, 0.94), width=1.6, stroke_opacity=op, fill_opacity=op*0.9)
    inner = pymupdf.Rect(cx-s*0.3, cy-s*0.3, cx+s*0.3, cy+s*0.3)
    sh.draw_rect(inner); sh.finish(color=ORANGE, fill=ORANGE, width=0.8, stroke_opacity=op, fill_opacity=op*0.18)
    sh.draw_circle((r.x0+s*0.12, r.y0+s*0.12), s*0.035); sh.finish(color=RUST, fill=RUST, stroke_opacity=op, fill_opacity=op)
    pins = max(4, int(s/9)); L = s*0.22; pts = []
    for k in range(pins):
        t = -s/2 + s*(k+0.5)/pins
        for (ax, ay, dx, dy) in ((cx+t, r.y0, 0, -1), (cx+t, r.y1, 0, 1), (r.x0, cy+t, -1, 0), (r.x1, cy+t, 1, 0)):
            sh.draw_line((ax, ay), (ax+dx*L, ay+dy*L)); pts.append((ax+dx*L, ay+dy*L, dx, dy))
    sh.finish(color=RUST, width=1.6, stroke_opacity=op, lineCap=0)
    sh.commit()
    nodes.append((cx, cy, s*0.9, op))
    return pts

# ---------------- PCB trace router ----------------
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
def route(x, y, d, steps, step):
    pts = [(x, y)]; run = 0; diag_left = 0
    for _ in range(steps):
        run += 1
        if d % 2 == 1:                       # on a 45-degree jog: return to orthogonal after a few steps
            diag_left -= 1
            if diag_left <= 0: d = (d + random.choice([-1, 1])) % 8; run = 0
        elif run >= 5 and random.random() < 0.16:
            d = (d + random.choice([-1, 1])) % 8; diag_left = random.randint(2, 4); run = 0
        dx, dy = DIRS[d]; s = step*(1.4142 if dx and dy else 1)
        nx, ny = x+dx*step, y+dy*step
        if C(nx, ny) < CL0+4: break
        x, y = nx, ny; pts.append((x, y))
    return pts, d
def draw_bus(x, y, d, n, gap, steps, step=10, color=None, op=0.6):
    """a bundle of parallel traces that bend together"""
    pts, d2 = route(x, y, d, steps, step)
    if len(pts) < 4: return 0
    P = np.array(pts, float)
    for k in range(n):
        off = (k-(n-1)/2)*gap
        # offset polyline perpendicular to each segment direction
        Q = []
        for i in range(len(P)):
            a = P[max(i-1, 0)]; b = P[min(i+1, len(P)-1)]
            t = b-a; t = t/ (np.linalg.norm(t)+1e-9); nrm = np.array([-t[1], t[0]])
            Q.append(P[i]+nrm*off)
        # trim where clearance drops
        good = [alpha_at(*q) > 0.02 for q in Q]
        segs, cur = [], []
        for q, g in zip(Q, good):
            if g: cur.append(q)
            elif cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        for sgm in segs:
            if len(sgm) < 3: continue
            a = op*np.mean([alpha_at(*q) for q in sgm])
            col = color or random.choice([RUST, RUST, ORANGE, SOFT])
            sh = pg.new_shape(); sh.draw_polyline([tuple(q) for q in sgm])
            sh.finish(color=col, width=1.5, stroke_opacity=a, lineCap=1, lineJoin=1, closePath=False)
            for end in (sgm[0], sgm[-1]):
                sh.draw_circle(tuple(end), 3.6); sh.finish(color=col, fill=(1, 1, 1), width=1.3, stroke_opacity=a, fill_opacity=a)
            sh.commit()
            if random.random() < 0.35: nodes.append((*sgm[-1], 9, a))
    return 1

# chips at the roomiest free spots (local maxima of clearance)
from scipy import ndimage
mx = ndimage.maximum_filter(clear, size=260)
cand = np.argwhere((clear == mx) & (clear > 70))
cand = sorted(cand.tolist(), key=lambda p: -clear[p[0], p[1]])
chips = []
for yy, xx in cand:
    if 2420 < xx < 2750 and 880 < yy < 1260: continue           # wafer column
    if any(math.hypot(xx-a, yy-b) < 380 for a, b, _ in chips): continue
    if xx < 110 or xx > W-110: continue
    s = min(70, clear[yy, xx]*0.75)
    chips.append((xx, yy, s))
    if len(chips) >= 6: break
print('chips', [(int(a), int(b), int(s)) for a, b, s in chips])
for cx, cy, s in chips:
    pins = chip(cx, cy, s, 0.75)
    # buses leaving the chip sides
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d = DIRS.index((dx, dy))
        draw_bus(cx+dx*(s/2+s*0.22+6), cy+dy*(s/2+s*0.22+6), d, random.randint(4, 6), 7, random.randint(18, 40), op=0.75)

# fill free space with buses seeded by noise-weighted sampling
free = np.argwhere(clear > CL1*0.6)
weights = np.ones(len(free))
# denser towards outer edges of the upper area
ys, xs = free[:, 0], free[:, 1]
edge = np.minimum.reduce([xs, W-xs, (ys-88)*2.5, (YMAX-ys)*2.5]).astype(float)
weights = 0.35 + np.exp(-edge/260)
weights /= weights.sum()
for idx in rng.choice(len(free), size=120, p=weights, replace=False):
    y, x = free[idx]
    x, y = round(x/7)*7, round(y/7)*7
    draw_bus(float(x), float(y), random.randrange(0, 8, 2), random.choice([2, 3, 3, 4, 5]), 7, random.randint(14, 40),
             op=random.uniform(0.35, 0.6))

# ---------------- soft hexagon "nano-grid" in the largest open areas ----------------
sh = pg.new_shape()
R = 16; hx = R*math.sqrt(3)
for j in range(int(H/(1.5*R))+2):
    for i in range(int(W/hx)+2):
        cx = i*hx + (hx/2 if j % 2 else 0); cy = j*1.5*R
        a = alpha_at(cx, cy)
        if a < 0.55 or random.random() > 0.45: continue
        pts = [(cx+R*math.cos(math.radians(60*k+30)), cy+R*math.sin(math.radians(60*k+30))) for k in range(6)]
        sh.draw_polyline(pts+[pts[0]]); sh.finish(color=ORANGE, width=0.6, stroke_opacity=0.10*a, closePath=True)
sh.commit()

# ---------------- LED-like glow nodes (raster, soft) ----------------
for x, y, r, a in nodes:
    gd.ellipse((x-r, y-r, x+r, y+r), fill=(245, 120, 40, int(200*a)))
g1 = glow.filter(ImageFilter.GaussianBlur(10)); g2 = glow.filter(ImageFilter.GaussianBlur(28))
G = np.maximum(np.asarray(g1, np.float32), np.asarray(g2, np.float32))
# keep glow off content
m = np.clip((clear-CL0)/(CL1-CL0), 0, 1)
G[..., 3] *= m*0.85
Image.fromarray(G.astype(np.uint8), 'RGBA').save('v2/glow.png')
pg.insert_image(pg.rect, filename='v2/glow.png', overlay=False)
for x, y, r, a in nodes:     # crisp bright cores
    s = pg.new_shape(); s.draw_circle((x, y), 2.4); s.finish(color=AMBER, fill=(1, 0.93, 0.8), width=0.8, stroke_opacity=a, fill_opacity=a); s.commit()
doc.save('v2/design.pdf', deflate=True, garbage=3)
print('nodes', len(nodes))
