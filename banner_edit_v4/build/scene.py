# Procedurally generated (original) glowing-chip-on-circuit-board scene for the banner's left panel.
# Board is drawn flat in board space, warped through a pinhole camera, then 3D parts are projected on top.
import numpy as np, math, random, io
from PIL import Image, ImageDraw, ImageFilter, ImageChops
random.seed(3); rng = np.random.default_rng(3)
OUT = 'v4/'
# ---------- panel / screen ----------
PX0, PY0, PX1, PY1 = 0, 86, 1010, 1131         # panel in page pt
S = 3                                            # screen px per pt
SW, SH = (PX1-PX0)*S, (PY1-PY0)*S
# ---------- camera ----------
T = math.radians(50); D = 1900.0; F = 890.0; CXs, CYs = 505.0, 236.0   # chip centre on page (pt)
ct, st = math.cos(T), math.sin(T)
def proj(X, Y, Z=0.0):
    dY = Y + D*ct; dZ = Z - D*st
    xc = X; yc = dY*st + dZ*ct; zc = dY*ct - dZ*st
    return ((CXs + F*xc/zc - PX0)*S, (CYs - F*yc/zc - PY0)*S)
# ---------- board texture ----------
BX0, BX1, BY0, BY1 = -1350, 1350, -1450, 560
TU = 2.4                                         # texture px per board unit
TW, TH = int((BX1-BX0)*TU), int((BY1-BY0)*TU)
def tpx(X, Y): return ((X-BX0)*TU, (BY1-Y)*TU)
base = Image.new('RGB', (TW, TH), (20, 9, 6))
emit = Image.new('RGB', (TW, TH), (0, 0, 0))      # self-lit (glowing) layer
lines = Image.new('L', (TW, TH), 0)               # all copper, for the light-mode continuation
bd, ed, ld = ImageDraw.Draw(base), ImageDraw.Draw(emit), ImageDraw.Draw(lines)
# faint fibre-glass weave / grid
for k in range(int(BX0), int(BX1), 40):
    bd.line([tpx(k, BY0), tpx(k, BY1)], fill=(26, 12, 8), width=1)
for k in range(int(BY0), int(BY1), 40):
    bd.line([tpx(BX0, k), tpx(BX1, k)], fill=(26, 12, 8), width=1)

PKG = 170                      # chip package half-size (board units)
occupied = []                  # component rectangles to keep clear
def free(x0, y0, x1, y1, pad=10):
    if max(abs(x0), abs(x1)) < PKG+60 and max(abs(y0), abs(y1)) < PKG+60: return False
    for a in occupied:
        if not (x1+pad < a[0] or x0-pad > a[2] or y1+pad < a[1] or y0-pad > a[3]): return False
    return True
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
def route(x, y, d, n, step=12, straight=4):
    pts = [(x, y)]; run = 0; diag = 0
    for i in range(n):
        run += 1
        if d % 2:
            diag -= 1
            if diag <= 0: d = (d+random.choice([-1, 1])) % 8; run = 0
        elif run >= straight and random.random() < 0.13:
            d = (d+random.choice([-1, 1])) % 8; diag = random.randint(2, 5); run = 0
        dx, dy = DIRS[d]; x += dx*step; y += dy*step
        if not (BX0 < x < BX1 and BY0 < y < BY1): break
        if max(abs(x), abs(y)) < PKG+20: break
        pts.append((x, y))
    return pts
def draw_trace(pts, width, glow, hot=False):
    if len(pts) < 2: return
    tp = [tpx(*p) for p in pts]
    bd.line(tp, fill=(70, 32, 18), width=max(1, int(width*TU)), joint='curve')
    ld.line(tp, fill=255, width=max(1, int(width*TU)), joint='curve')
    if glow > 0:
        # brightness falls off along the trace away from the chip
        for i in range(len(tp)-1):
            g = glow*math.exp(-i/22.0)
            if g < 0.04: break
            c = (int(255*g), int((150 if not hot else 200)*g), int((60 if not hot else 120)*g))
            ed.line([tp[i], tp[i+1]], fill=c, width=max(1, int(width*0.8*TU)))
    ex, ey = tp[-1]; r = (width*1.9)*TU
    bd.ellipse((ex-r, ey-r, ex+r, ey+r), fill=(110, 52, 26)); ld.ellipse((ex-r, ey-r, ex+r, ey+r), fill=255)
    bd.ellipse((ex-r*0.45, ey-r*0.45, ex+r*0.45, ey+r*0.45), fill=(14, 6, 4))
# ---- traces fanning out from every side of the chip ----
for side in range(4):
    nrm = [(0, 1), (1, 0), (0, -1), (-1, 0)][side]; tan = (nrm[1], -nrm[0])
    d0 = DIRS.index(nrm)
    for k in range(-11, 12):
        start = (nrm[0]*(PKG+22) + tan[0]*k*14, nrm[1]*(PKG+22) + tan[1]*k*14)
        pts = route(*start, d0, random.randint(15, 70), step=12, straight=random.randint(3, 9))
        far = nrm[1] == 1          # traces heading to the far side are seen more compressed
        draw_trace(pts, random.choice([2.2, 2.6, 3.2]), random.uniform(0.55, 1.0) if random.random() < 0.75 else 0.0, hot=abs(k) < 4)
# ---- background traces / buses ----
for _ in range(260):
    x, y = random.uniform(BX0, BX1), random.uniform(BY0, BY1)
    if max(abs(x), abs(y)) < PKG+80: continue
    d = random.randrange(0, 8, 2); n = random.choice([1, 2, 3, 4, 6])
    base_pts = route(x, y, d, random.randint(8, 45), step=12)
    if len(base_pts) < 3: continue
    glow = random.uniform(0.25, 0.7) if random.random() < 0.25 else 0.0
    P = np.array(base_pts, float)
    for j in range(n):
        off = (j-(n-1)/2)*9
        Q = []
        for i in range(len(P)):
            t = P[min(i+1, len(P)-1)]-P[max(i-1, 0)]; t /= (np.linalg.norm(t)+1e-9)
            Q.append(tuple(P[i]+np.array([-t[1], t[0]])*off))
        draw_trace(Q, 2.0, glow)
# ---- flat components ----
def comp_rect(x0, y0, x1, y1, body, edge=None):
    bd.rectangle((*tpx(x0, y1), *tpx(x1, y0)), fill=body, outline=edge)
    ld.rectangle((*tpx(x0, y1), *tpx(x1, y0)), outline=200, width=2)
def smd(x, y, horiz):
    w, h = (34, 16) if horiz else (16, 34)
    if not free(x-w/2, y-h/2, x+w/2, y+h/2): return
    occupied.append((x-w/2, y-h/2, x+w/2, y+h/2))
    comp_rect(x-w/2, y-h/2, x+w/2, y+h/2, (40, 30, 26))
    if horiz:
        comp_rect(x-w/2, y-h/2, x-w/2+8, y+h/2, (170, 150, 135)); comp_rect(x+w/2-8, y-h/2, x+w/2, y+h/2, (170, 150, 135))
    else:
        comp_rect(x-w/2, y-h/2, x+w/2, y-h/2+8, (170, 150, 135)); comp_rect(x-w/2, y+h/2-8, x+w/2, y+h/2, (170, 150, 135))
def qfp(x, y, s):
    if not free(x-s/2-12, y-s/2-12, x+s/2+12, y+s/2+12): return
    occupied.append((x-s/2-12, y-s/2-12, x+s/2+12, y+s/2+12))
    n = int(s/9)
    for k in range(n):
        t = -s/2+s*(k+0.5)/n
        for (ax, ay, bx, by) in ((x+t, y+s/2, x+t, y+s/2+11), (x+t, y-s/2, x+t, y-s/2-11), (x+s/2, y+t, x+s/2+11, y+t), (x-s/2, y+t, x-s/2-11, y+t)):
            bd.line([tpx(ax, ay), tpx(bx, by)], fill=(160, 130, 110), width=max(1, int(2.4*TU)))
    comp_rect(x-s/2, y-s/2, x+s/2, y+s/2, (24, 18, 16), (60, 40, 32))
    cx_, cy_ = tpx(x-s/2+9, y+s/2-9); bd.ellipse((cx_-3*TU, cy_-3*TU, cx_+3*TU, cy_+3*TU), fill=(60, 44, 38))
def bga(x, y, nx, ny):
    w, h = nx*14, ny*14
    if not free(x, y, x+w, y+h): return
    occupied.append((x, y, x+w, y+h))
    for i in range(nx):
        for j in range(ny):
            px, py = tpx(x+i*14+7, y+j*14+7); r = 4.2*TU
            bd.ellipse((px-r, py-r, px+r, py+r), fill=(120, 72, 44)); ld.ellipse((px-r, py-r, px+r, py+r), fill=180)
            if random.random() < 0.12: ed.ellipse((px-r, py-r, px+r, py+r), fill=(255, 150, 70))
for _ in range(700):
    x, y = random.uniform(BX0+40, BX1-40), random.uniform(BY0+40, BY1-40)
    r = random.random()
    if r < 0.70: smd(x, y, random.random() < 0.5)
    elif r < 0.90: qfp(x, y, random.choice([48, 60, 80, 96]))
    else: bga(x, y, random.randint(4, 8), random.randint(3, 6))
# ---- chip light illuminating the board ----
Bi = np.asarray(base, np.float32)
yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
bx = xx/TU + BX0; by = BY1 - yy/TU
r = np.hypot(bx, by)
illum = 1.0 + 3.2/(1 + (r/330)**2)
warm = np.array([1.0, 0.70, 0.45])
Bi = np.clip(Bi*illum[..., None]*(0.75 + 0.25*warm), 0, 255)
base = Image.fromarray(Bi.astype(np.uint8))
del Bi, yy, xx, bx, by, r, illum

# ---------- warp board onto the screen ----------
def homography(src, dst):
    A, b = [], []
    for (u, v), (x, y) in zip(dst, src):
        A += [[u, v, 1, 0, 0, 0, -x*u, -x*v], [0, 0, 0, u, v, 1, -y*u, -y*v]]; b += [x, y]
    return tuple(np.linalg.solve(np.array(A, float), np.array(b, float)))
corners_b = [(BX0, BY1), (BX1, BY1), (BX1, BY0), (BX0, BY0)]
src = [tpx(*c) for c in corners_b]; dst = [proj(*c) for c in corners_b]
H = homography(src, dst)
def warp(img): return img.transform((SW, SH), Image.PERSPECTIVE, H, Image.BICUBIC)
board = np.asarray(warp(base), np.float32)
glow_board = np.asarray(warp(emit), np.float32)
copper = np.asarray(warp(lines), np.float32)/255
del base, emit, lines

# ---------- 3D parts in screen space ----------
scene = Image.fromarray(board.astype(np.uint8)).convert('RGBA'); sd = ImageDraw.Draw(scene)
hot = Image.new('RGB', (SW, SH)); hd = ImageDraw.Draw(hot)       # emissive (bloomed) layer
def poly(d, pts, fill, outline=None, w=1): d.polygon(pts, fill=fill, outline=outline, width=w)
def box(x0, y0, x1, y1, z0, z1, top, side_l, side_f, draw=sd):
    T_ = [proj(x0, y0, z1), proj(x1, y0, z1), proj(x1, y1, z1), proj(x0, y1, z1)]
    front = [proj(x0, y0, z0), proj(x1, y0, z0), proj(x1, y0, z1), proj(x0, y0, z1)]    # near face (Y = y0)
    poly(draw, front, side_f); poly(draw, T_, top)
    return T_
# capacitors (cylinders) and crystals spread on the board, drawn far-to-near
caps = []
for _ in range(16):
    X, Y = random.uniform(-1150, 1150), random.uniform(-500, 520)
    if math.hypot(X, Y) < 420: continue
    caps.append((X, Y, random.choice([26, 32, 40]), random.choice([50, 70, 90])))
for X, Y, R, Hh in sorted(caps, key=lambda c: -c[1]):
    n = 48
    top = [proj(X+R*math.cos(2*math.pi*k/n), Y+R*math.sin(2*math.pi*k/n), Hh) for k in range(n)]
    bot = [proj(X+R*math.cos(2*math.pi*k/n), Y+R*math.sin(2*math.pi*k/n), 0) for k in range(n)]
    # side: fill quads with shading by angle (light from the chip)
    la = math.atan2(-Y, -X)
    for k in range(n):
        a = 2*math.pi*(k+0.5)/n
        if math.sin(a) > 0.15: continue                       # back side hidden
        shade = 0.35 + 0.65*max(0, math.cos(a-la))
        c = (int(60+150*shade), int(40+95*shade), int(30+60*shade))
        sd.polygon([bot[k], bot[(k+1) % n], top[(k+1) % n], top[k]], fill=c)
    sd.polygon(top, fill=(150, 120, 105), outline=(210, 180, 160))
    ins = [proj(X+R*0.55*math.cos(2*math.pi*k/n), Y+R*0.55*math.sin(2*math.pi*k/n), Hh) for k in range(n)]
    sd.line(ins+[ins[0]], fill=(100, 80, 70), width=2)
    sd.line([proj(X-R*0.55, Y, Hh), proj(X+R*0.55, Y, Hh)], fill=(100, 80, 70), width=2)
for _ in range(6):   # crystal oscillators / inductors
    X, Y = random.uniform(-1100, 1100), random.uniform(-300, 480)
    if math.hypot(X, Y) < 450: continue
    box(X-45, Y-22, X+45, Y+22, 0, 26, (175, 160, 150), None, (95, 80, 72))
# the main chip: substrate + pins + glowing lid
pins = 22
for side in range(4):
    for k in range(pins):
        t = -PKG+10+(2*PKG-20)*k/(pins-1)
        a, b2 = [((t, -PKG), (t, -PKG-16)), ((t, PKG), (t, PKG+16)), ((-PKG, t), (-PKG-16, t)), ((PKG, t), (PKG+16, t))][side]
        sd.line([proj(*a, 4), proj(*b2, 2)], fill=(235, 190, 150), width=max(1, int(1.6*S)))
        hd.line([proj(*a, 4), proj(*b2, 2)], fill=(120, 60, 20), width=max(1, int(1.6*S)))
box(-PKG, -PKG, PKG, PKG, 0, 18, (52, 30, 22), None, (90, 46, 26))
box(-PKG+8, -PKG+8, PKG-8, PKG-8, 18, 24, (70, 40, 28), None, (150, 70, 30))
L = 128
top = box(-L, -L, L, L, 24, 52, (255, 236, 205), None, (255, 150, 60))
# glowing lid: radial hot gradient
lid = Image.new('L', (SW, SH)); ImageDraw.Draw(lid).polygon(top, fill=255)
cxp, cyp = proj(0, 0, 52)
gy, gx = np.mgrid[0:SH, 0:SW].astype(np.float32)
rad = np.hypot((gx-cxp)/ (F*L/ (D)*S*1.15), (gy-cyp)/(F*L/D*S*0.85))
lidc = np.dstack([np.full_like(rad, 250), 238-95*np.clip(rad, 0, 1)**1.3, 215-150*np.clip(rad, 0, 1)**1.3])
lidm = np.asarray(lid, np.float32)/255
sc = np.asarray(scene, np.float32)
sc[..., :3] = sc[..., :3]*(1-lidm[..., None]) + lidc*lidm[..., None]
scene = Image.fromarray(sc.astype(np.uint8))
hd.polygon(top, fill=(150, 80, 30))
front = [proj(-L, -L, 24), proj(L, -L, 24), proj(L, -L, 52), proj(-L, -L, 52)]
hd.polygon(front, fill=(255, 120, 40))
sd = ImageDraw.Draw(scene)
sd.line(top+[top[0]], fill=(255, 250, 240), width=2*S)
for k in range(1, 8):
    t = -L + 2*L*k/8
    sd.line([proj(t, -L+14, 52), proj(t, L-14, 52)], fill=(255, 205, 150), width=1)
    sd.line([proj(-L+14, t, 52), proj(L-14, t, 52)], fill=(255, 205, 150), width=1)
# rising light beams
beams = Image.new('RGB', (SW, SH)); bdw = ImageDraw.Draw(beams)
for _ in range(46):
    X, Y = random.uniform(-L, L), random.uniform(-L, L)
    x0, y0 = proj(X, Y, 52); hgt = random.uniform(0.25, 1.0)*y0
    for seg in range(24):
        f0, f1 = seg/24, (seg+1)/24
        a = (1-f0)**1.6*random.uniform(0.5, 1.0)
        bdw.line([(x0, y0-hgt*f0), (x0, y0-hgt*f1)], fill=(int(255*a), int(190*a), int(120*a)), width=random.choice([1, 2, 3]))
for _ in range(30):                 # thinner beams from glowing points on the board
    X, Y = random.uniform(-700, 700), random.uniform(-200, 450)
    if max(abs(X), abs(Y)) < PKG+30: continue
    x0, y0 = proj(X, Y, 0); hgt = random.uniform(40, 160)*S
    for seg in range(12):
        f0, f1 = seg/12, (seg+1)/12; a = (1-f0)**2*0.6
        bdw.line([(x0, y0-hgt*f0), (x0, y0-hgt*f1)], fill=(int(255*a), int(150*a), int(70*a)), width=1)
# ---------- bloom / compositing (dark version) ----------
emis = np.asarray(hot, np.float32) + glow_board
E = Image.fromarray(np.clip(emis, 0, 255).astype(np.uint8))
b1 = np.asarray(E.filter(ImageFilter.GaussianBlur(2*S)), np.float32)
b2 = np.asarray(E.filter(ImageFilter.GaussianBlur(9*S)), np.float32)
b3 = np.asarray(E.filter(ImageFilter.GaussianBlur(30*S)), np.float32)
Bm = np.asarray(beams, np.float32); Bb = np.asarray(beams.filter(ImageFilter.GaussianBlur(3*S)), np.float32)
dark = np.asarray(scene.convert('RGB'), np.float32)
dark = dark + emis*0.9 + b1*0.9 + b2*1.0 + b3*1.2 + Bm*1.8 + Bb*2.2
# big soft halo around the chip
rr = np.hypot((gx-cxp)/(260*S), (gy-cyp)/(150*S))
dark += np.dstack([255*np.exp(-rr**2*2.2), 140*np.exp(-rr**2*2.2), 60*np.exp(-rr**2*2.2)])*0.55
# tone-map to keep highlights from clipping harshly
dark = 255*(1-np.exp(-dark/185.0))
# slight vignette towards the panel edges
vx = np.clip(1 - ((gx/SW-0.5)*1.4)**4, 0, 1); dark *= (0.55 + 0.45*vx)[..., None]
np.save(OUT+'dark.npy', dark.astype(np.uint8)); np.save(OUT+'copper.npy', (copper*255).astype(np.uint8))
np.save(OUT+'glowboard.npy', np.clip(glow_board, 0, 255).astype(np.uint8))
Image.fromarray(dark.astype(np.uint8)).resize((SW//3, SH//3)).save(OUT+'dark_preview.png')
print('done', SW, SH)
