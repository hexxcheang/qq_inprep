# Futuristic semiconductor background for the left (circled) panel of the v3 banner.
import pymupdf, numpy as np, math, random
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage
random.seed(11); rng = np.random.default_rng(11)
SRC = 'v3/banner.pdf'
X0, Y0, X1, Y1 = 0, 86, 1010, 1131          # panel region (pt, top-left origin)
src = pymupdf.open(SRC); sp = src[0]; PW, PH = sp.rect.width, sp.rect.height

# ---------- content proximity (art is softened, never removed, under text/logos) ----------
Z = 1
pix = sp.get_pixmap(matrix=pymupdf.Matrix(Z, Z), alpha=False, clip=pymupdf.Rect(X0, Y0, X1, Y1))
a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3)
content = a.min(2) < 200
for i in sp.get_image_info(xrefs=True):
    if i['xref'] in (187, 188, 387):      # logo boxes (made transparent later) – mark logo pixels only
        pass
dist = ndimage.distance_transform_edt(~content)
def soft(x, y):           # 0.28 right on top of content -> 1 in the open
    xi, yi = int(x-X0), int(y-Y0)
    if 0 <= xi < dist.shape[1] and 0 <= yi < dist.shape[0]:
        return 0.12 + 0.88*min(1, max(0, (dist[yi, xi]-4)/60))
    return 1.0
def panel(x, y):          # panel shape: soft fade at the right and bottom
    fx = min(1, max(0, (1000-x)/110)); fy = min(1, max(0, (1122-y)/70))
    s = lambda t: t*t*(3-2*t)
    return s(fx)*s(fy)*(1 if y >= Y0 else 0)
def A(x, y): return panel(x, y)*soft(x, y)

RUST = (0.663, 0.125, 0.0); ORANGE = (0.91, 0.39, 0.11); AMBER = (0.97, 0.62, 0.27)
PEACH = (0.99, 0.84, 0.74); DEEP = (0.42, 0.10, 0.03)
doc = pymupdf.open(); pg = doc.new_page(width=PW, height=PH)

# ================= raster base: tint, light bands, glow ==================
S = 3                                             # px per pt
w, h = (X1-X0)*S, (Y1-Y0)*S
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); X = xx/S+X0; Y = yy/S+Y0
fx = np.clip((1000-X)/110, 0, 1); fy = np.clip((1122-Y)/70, 0, 1)
P = (fx*fx*(3-2*fx))*(fy*fy*(3-2*fy))
# warm gradient: deeper peach at the top-left and edges, near-white around the centre
r_c = np.hypot((X-470)/560, (Y-560)/520)
tint = np.clip(0.10 + 0.55*np.clip(r_c-0.25, 0, 1)**1.2, 0, 0.62)
col = np.zeros((h, w, 3), np.float32)
base_a = np.array([0.985, 0.80, 0.68]); base_b = np.array([1.0, 0.95, 0.91])
col[:] = base_b + (base_a-base_b)*np.clip(r_c-0.2, 0, 1)[..., None]
alpha = tint*P
# diagonal light bands (as in the reference banners), slant ~ 62 deg
def band(c0, width, strength, colr):
    global col, alpha
    d = (X*0.88 + Y*0.47) - c0                       # distance along the band normal
    m = np.clip(1 - np.abs(d)/width, 0, 1)**0.6 * strength * P
    col = col*(1-m[..., None]) + np.array(colr)*m[..., None]
    alpha = np.maximum(alpha, m*0.9)
band(1030, 34, 0.30, (0.96, 0.55, 0.30))
band(1105, 10, 0.32, (0.91, 0.39, 0.11))
band(300, 22, 0.22, (0.96, 0.60, 0.36))
band(1420, 60, 0.16, (0.98, 0.70, 0.50))
# halo behind the EPTC logo
g = np.exp(-(((X-470)/380)**2 + ((Y-512)/190)**2)*1.6)
col = col*(1-0.25*g[..., None]) + np.array([1.0, 0.86, 0.72])*0.25*g[..., None]
img = np.dstack([np.clip(col, 0, 1), np.clip(alpha, 0, 1)])
Image.fromarray((img*255).astype(np.uint8), 'RGBA').save('v3/base.png')
pg.insert_image(pymupdf.Rect(X0, Y0, X1, Y1), filename='v3/base.png')

glow = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(glow); nodes = []
def node(x, y, r, a): nodes.append((x, y, r, a))

def sh(): return pg.new_shape()

# ================= wafer ring framing the EPTC logo ==================
WX, WY, WR = 470, 512, 392
s = sh()
pitch = 30
for i in range(-14, 15):
    for j in range(-14, 15):
        x0, y0 = WX+i*pitch-pitch/2, WY+j*pitch-pitch/2
        if all(math.hypot(px-WX, py-WY) < WR-16 for px, py in ((x0, y0), (x0+pitch, y0), (x0, y0+pitch), (x0+pitch, y0+pitch))):
            aa = A(x0+pitch/2, y0+pitch/2)
            if aa <= 0.02: continue
            hot = random.random() < 0.07
            s.draw_rect(pymupdf.Rect(x0+1.6, y0+1.6, x0+pitch-1.6, y0+pitch-1.6))
            s.finish(color=ORANGE, fill=AMBER if hot else None, width=0.6, stroke_opacity=0.22*aa, fill_opacity=0.30*aa)
            if hot: node(x0+pitch/2, y0+pitch/2, 9, 0.6*aa)
s.commit()
s = sh()
for k, (rr, wdt, op, col_) in enumerate([(WR, 3.2, 0.55, RUST), (WR-9, 1.0, 0.45, ORANGE), (WR+14, 0.8, 0.30, ORANGE)]):
    # draw as polyline so opacity can follow the panel/content mask
    N = 360
    for t in range(N):
        a0, a1 = 2*math.pi*t/N, 2*math.pi*(t+1)/N
        if k == 0 and abs(a0 - math.pi/2) < 0.03: continue                 # wafer notch
        p0 = (WX+rr*math.cos(a0), WY+rr*math.sin(a0)); p1 = (WX+rr*math.cos(a1), WY+rr*math.sin(a1))
        aa = A(*p0)
        if aa < 0.02: continue
        s.draw_line(p0, p1); s.finish(color=col_, width=wdt, stroke_opacity=op*aa, lineCap=1)
        if k == 2 and t % 12 == 0: node(*p0, 6, 0.5*aa)
s.commit()
# tick marks around ring (alignment marks)
s = sh()
for t in range(0, 360, 6):
    a0 = math.radians(t); L = 14 if t % 30 == 0 else 7
    p0 = (WX+(WR+20)*math.cos(a0), WY+(WR+20)*math.sin(a0)); p1 = (WX+(WR+20+L)*math.cos(a0), WY+(WR+20+L)*math.sin(a0))
    aa = A(*p1)
    if aa > 0.02: s.draw_line(p0, p1); s.finish(color=RUST, width=1.1, stroke_opacity=0.45*aa)
s.commit()

# ================= isometric chiplet package (top-right hero) ==================
CX, CY, K = 790, 236, 0.9
c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
def iso(x, y, z): return (CX + (x-y)*c30*K, CY + (x+y)*s30*K - z*K)
def block(x, y, z, dx, dy, dz, top, left, right, edge=RUST, op=0.95, lw=0.9):
    s = sh()
    T = [iso(x, y, z+dz), iso(x+dx, y, z+dz), iso(x+dx, y+dy, z+dz), iso(x, y+dy, z+dz)]
    Lf = [iso(x, y+dy, z), iso(x+dx, y+dy, z), iso(x+dx, y+dy, z+dz), iso(x, y+dy, z+dz)]
    Rf = [iso(x+dx, y, z), iso(x+dx, y+dy, z), iso(x+dx, y+dy, z+dz), iso(x+dx, y, z+dz)]
    for poly, c in ((Lf, left), (Rf, right), (T, top)):
        s.draw_polyline(poly+[poly[0]]); s.finish(color=edge, fill=c, width=lw, fill_opacity=op, stroke_opacity=op, closePath=True, lineJoin=1)
    s.commit()
# substrate
block(-120, -120, -40, 240, 240, 22, (0.99, 0.86, 0.76), (0.86, 0.42, 0.20), (0.93, 0.56, 0.32))
# BGA balls under substrate (visible front edges)
s = sh()
for i in range(12):
    for (px, py) in ((-120+10+i*20, 120), (120, -120+10+i*20)):
        q = iso(px, py, -46); s.draw_circle(q, 3.2); s.finish(color=RUST, fill=(0.95, 0.8, 0.7), width=0.6, fill_opacity=0.9, stroke_opacity=0.9)
s.commit()
# substrate surface traces
s = sh()
for k in range(-100, 101, 14):
    s.draw_line(iso(k, -112, -18), iso(k, -70, -18)); s.draw_line(iso(-112, k, -18), iso(-70, k, -18))
s.finish(color=ORANGE, width=0.7, stroke_opacity=0.65)
s.commit()
# interposer
block(-78, -78, -18, 156, 156, 10, (1.0, 0.93, 0.87), (0.80, 0.36, 0.17), (0.90, 0.50, 0.27))
# HBM stacks + central SoC die
for (hx, hy) in ((-68, -68), (30, -68), (-68, 30)):
    for lvl in range(5):
        block(hx, hy, -8+lvl*7, 38, 38, 6, (0.98, 0.80, 0.66) if lvl < 4 else (1.0, 0.90, 0.80), (0.70, 0.27, 0.10), (0.84, 0.42, 0.20), lw=0.7)
block(-8, -8, -8, 66, 66, 16, (0.95, 0.47, 0.17), (0.60, 0.15, 0.02), (0.78, 0.28, 0.06), edge=DEEP)
# die surface grid + glow
s = sh()
for k in range(1, 6):
    t = -8+k*11
    s.draw_line(iso(t, -8, 8.2), iso(t, 58, 8.2)); s.draw_line(iso(-8, t, 8.2), iso(58, t, 8.2))
s.finish(color=(1, 0.85, 0.6), width=0.6, stroke_opacity=0.8)
s.commit()
node(*iso(25, 25, 10), 46, 0.9); node(*iso(25, 25, 10), 18, 1.0)
# fan-out traces from the package to the left (data bus)
s = sh()
for k in range(9):
    yk = 150 + k*10
    p_start = iso(-120, -120+20+k*22, -30)
    pts = [p_start, (p_start[0]-40-k*4, p_start[1]), (p_start[0]-70-k*4, p_start[1]-30+k*2), (420-k*10, p_start[1]-30+k*2)]
    aa = min(A(*pp) for pp in pts)
    s.draw_polyline(pts); s.finish(color=ORANGE if k % 3 else RUST, width=1.4, stroke_opacity=0.7*aa, lineCap=1, lineJoin=1, closePath=False)
    s.draw_circle(pts[-1], 3.4); s.finish(color=RUST, fill=(1, 1, 1), width=1.1, stroke_opacity=0.7*aa, fill_opacity=0.9*aa)
    if k % 2 == 0: node(*pts[-1], 8, 0.7*aa)
s.commit()

# ================= BGA pad array (top-left corner) ==================
s = sh()
for i in range(16):
    for j in range(6):
        x, y = 40+i*16, 112+j*16
        if (i+j) % 7 == 0: continue
        aa = A(x, y)*(1-j/8)
        s.draw_circle((x, y), 4.2); s.finish(color=RUST, fill=PEACH, width=0.8, stroke_opacity=0.45*aa, fill_opacity=0.55*aa)
s.commit()

# ================= PCB trace router across the panel ==================
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
def route(x, y, d, steps, step=9):
    pts = [(x, y)]; run = 0; diag = 0
    for _ in range(steps):
        run += 1
        if d % 2: 
            diag -= 1
            if diag <= 0: d = (d+random.choice([-1, 1])) % 8; run = 0
        elif run >= 6 and random.random() < 0.15: d = (d+random.choice([-1, 1])) % 8; diag = random.randint(2, 4); run = 0
        dx, dy = DIRS[d]; x, y = x+dx*step, y+dy*step
        if panel(x, y) < 0.05 or y < Y0+6: break
        if math.hypot(x-CX, y-CY) < 150: break
        if ((x-470)/400)**2 + ((y-640)/300)**2 < 1: break
        pts.append((x, y))
    return pts
def bus(x, y, d, n, gap, steps, op):
    P0 = np.array(route(x, y, d, steps), float)
    if len(P0) < 5: return
    for k in range(n):
        off = (k-(n-1)/2)*gap; Q = []
        for i in range(len(P0)):
            t = P0[min(i+1, len(P0)-1)]-P0[max(i-1, 0)]; t /= (np.linalg.norm(t)+1e-9)
            Q.append(P0[i]+np.array([-t[1], t[0]])*off)
        aa = op*np.mean([A(*q) for q in Q])
        if aa < 0.03: continue
        s = sh(); s.draw_polyline([tuple(q) for q in Q])
        c = random.choice([RUST, RUST, ORANGE])
        s.finish(color=c, width=1.3, stroke_opacity=aa, lineCap=1, lineJoin=1, closePath=False)
        for e in (Q[0], Q[-1]):
            s.draw_circle(tuple(e), 3.2); s.finish(color=c, fill=(1, 1, 1), width=1.1, stroke_opacity=aa, fill_opacity=aa)
        s.commit()
        if random.random() < 0.3: node(*Q[-1], 7, aa)
# density: rich near the left edge, the top strip and the lower strip
def central(x, y): return ((x-470)/430)**2 + ((y-640)/330)**2 < 1     # logo + title zone
for _ in range(65):
    while True:
        zone = random.random()
        if zone < 0.40:   x, y = random.uniform(5, 120), random.uniform(120, 1110)
        elif zone < 0.70: x, y = random.uniform(30, 600), random.uniform(110, 330)
        else:             x, y = random.uniform(20, 940), random.uniform(1040, 1112)
        if not central(x, y): break
    x, y = round(x/9)*9, round(y/9)*9
    bus(x, y, random.randrange(0, 8, 2), random.choice([2, 3, 4, 5]), 7, random.randint(14, 44), random.uniform(0.35, 0.6))

# ================= light streaks along the band edges ==================
s = sh()
for c0, L, op in ((1030-34, 1, 0.6), (1030+34, 1, 0.5), (1105, 1, 0.7), (300+22, 1, 0.45)):
    # line X*0.88 + Y*0.47 = c0  ->  parametrise by y
    pts = [((c0-y*0.47)/0.88, y) for y in np.linspace(Y0, 1125, 120)]
    for p0, p1 in zip(pts, pts[1:]):
        aa = panel(*p0)
        if aa < 0.03 or p0[0] < 0: continue
        s.draw_line(p0, p1); s.finish(color=ORANGE, width=1.2, stroke_opacity=op*aa)
    for y in np.linspace(Y0+40, 1100, 5):
        p = ((c0-y*0.47)/0.88, y)
        if 0 < p[0] < 990 and panel(*p) > 0.2: node(*p, 12, 0.55*panel(*p))
s.commit()

# ================= hexagon nano-grid (very faint) ==================
s = sh(); R = 15; hx = R*math.sqrt(3)
for j in range(int((Y1-Y0)/(1.5*R))+2):
    for i in range(int((X1-X0)/hx)+2):
        cx = X0+i*hx+(hx/2 if j % 2 else 0); cy = Y0+j*1.5*R
        aa = A(cx, cy)*(0.4+0.6*min(1, math.hypot(cx-470, cy-560)/450))
        if aa < 0.25 or random.random() > 0.55: continue
        pts = [(cx+R*math.cos(math.radians(60*k+30)), cy+R*math.sin(math.radians(60*k+30))) for k in range(6)]
        s.draw_polyline(pts+[pts[0]]); s.finish(color=ORANGE, width=0.5, stroke_opacity=0.12*aa, closePath=True)
s.commit()

# ================= glows (raster) + bright cores ==================
for x, y, r, aa in nodes:
    gx, gy = (x-X0)*S, (y-Y0)*S
    gd.ellipse((gx-r*S, gy-r*S, gx+r*S, gy+r*S), fill=(246, 125, 40, int(210*min(1, aa))))
G = np.maximum(np.asarray(glow.filter(ImageFilter.GaussianBlur(8*S)), np.float32), np.asarray(glow.filter(ImageFilter.GaussianBlur(3*S)), np.float32))
G[..., 3] *= P
Image.fromarray(np.clip(G, 0, 255).astype(np.uint8), 'RGBA').save('v3/glow.png')
pg.insert_image(pymupdf.Rect(X0, Y0, X1, Y1), filename='v3/glow.png')
for x, y, r, aa in nodes:
    if r > 20: continue
    s = sh(); s.draw_circle((x, y), 2.2); s.finish(color=AMBER, fill=(1, 0.95, 0.85), width=0.7, stroke_opacity=aa, fill_opacity=aa); s.commit()
doc.save('v3/design.pdf', deflate=True, garbage=3)
print('nodes', len(nodes))
