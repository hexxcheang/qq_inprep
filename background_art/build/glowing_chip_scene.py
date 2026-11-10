# Futuristic glowing-chip circuit-board scene (original, procedurally generated), warm EPTC palette.
import numpy as np, math, random, sys
from PIL import Image, ImageDraw, ImageFilter
random.seed(5); rng = np.random.default_rng(5)
OUT = 'v5/'
SW, SH = 3840, 2160
# ---------------- camera ----------------
T = math.radians(44); D = 1900.0; F = 3150.0; CX, CY = SW/2, SH*0.47
ct, st = math.cos(T), math.sin(T)
def proj(X, Y, Z=0.0):
    dY = Y + D*ct; dZ = Z - D*st
    yc = dY*st + dZ*ct; zc = dY*ct - dZ*st
    return (CX + F*X/zc, CY - F*yc/zc)
def depth(X, Y, Z=0.0): return (Y + D*ct)*ct - (Z - D*st)*st
# ---------------- board texture ----------------
BX0, BX1, BY0, BY1 = -2300, 2300, -900, 2600
TU = 1.9
TW, TH = int((BX1-BX0)*TU), int((BY1-BY0)*TU)
def tp(X, Y): return ((X-BX0)*TU, (BY1-Y)*TU)
base = Image.new('RGB', (TW, TH), (16, 7, 6)); emit = Image.new('RGB', (TW, TH)); bd, ed = ImageDraw.Draw(base), ImageDraw.Draw(emit)
# glowing perspective grid (tron-like), very faint, plus fibre weave
for k in range(int(BX0), int(BX1)+1, 40): bd.line([tp(k, BY0), tp(k, BY1)], fill=(22, 10, 8))
for k in range(int(BY0), int(BY1)+1, 40): bd.line([tp(BX0, k), tp(BX1, k)], fill=(22, 10, 8))
for k in range(-2400, 2401, 240): ed.line([tp(k, BY0), tp(k, BY1)], fill=(38, 14, 6), width=2)
for k in range(-960, 2601, 240): ed.line([tp(BX0, k), tp(BX1, k)], fill=(38, 14, 6), width=2)
PKG = 175
occupied = []
def free(x0, y0, x1, y1, pad=10):
    if max(abs(x0), abs(x1)) < 560 and max(abs(y0), abs(y1)) < 560: return False   # keep HUD rings area clean
    return all(x1+pad < a[0] or x0-pad > a[2] or y1+pad < a[1] or y0-pad > a[3] for a in occupied)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
def route(x, y, d, n, step=12, straight=5):
    pts = [(x, y)]; run = 0; diag = 0
    for i in range(n):
        run += 1
        if d % 2:
            diag -= 1
            if diag <= 0: d = (d+random.choice([-1, 1])) % 8; run = 0
        elif run >= straight and random.random() < 0.12: d = (d+random.choice([-1, 1])) % 8; diag = random.randint(2, 5); run = 0
        dx, dy = DIRS[d]; x += dx*step; y += dy*step
        if not (BX0 < x < BX1 and BY0 < y < BY1) or max(abs(x), abs(y)) < PKG+20: break
        pts.append((x, y))
    return pts
pulses = []
def trace(pts, w, glow, hot=False, pulse=False):
    if len(pts) < 2: return
    t = [tp(*p) for p in pts]
    bd.line(t, fill=(64, 28, 16), width=max(1, int(w*TU)), joint='curve')
    if glow > 0:
        for i in range(len(t)-1):
            g = glow*math.exp(-i/26.0)
            if g < 0.04: break
            ed.line([t[i], t[i+1]], fill=(int(255*g), int((205 if hot else 140)*g), int((130 if hot else 50)*g)), width=max(1, int(w*0.8*TU)))
    if pulse and len(t) > 8: pulses.append(t)
    ex, ey = t[-1]; r = w*1.9*TU
    bd.ellipse((ex-r, ey-r, ex+r, ey+r), fill=(105, 50, 26)); bd.ellipse((ex-r*.45, ey-r*.45, ex+r*.45, ey+r*.45), fill=(12, 5, 4))
# fan-out from the chip
for side in range(4):
    nrm = [(0, 1), (1, 0), (0, -1), (-1, 0)][side]; tan = (nrm[1], -nrm[0]); d0 = DIRS.index(nrm)
    for k in range(-12, 13):
        st0 = (nrm[0]*(PKG+22)+tan[0]*k*13, nrm[1]*(PKG+22)+tan[1]*k*13)
        trace(route(*st0, d0, random.randint(25, 110), straight=random.randint(4, 10)), random.choice([2.2, 2.8, 3.4]),
              random.uniform(0.6, 1.0) if random.random() < 0.8 else 0, hot=abs(k) < 4, pulse=random.random() < 0.55)
# background buses
for _ in range(520):
    x, y = random.uniform(BX0, BX1), random.uniform(BY0, BY1)
    if max(abs(x), abs(y)) < 600: continue
    base_pts = route(x, y, random.randrange(0, 8, 2), random.randint(8, 50))
    if len(base_pts) < 3: continue
    n = random.choice([1, 2, 3, 4, 6, 8]); glow = random.uniform(0.25, 0.75) if random.random() < 0.3 else 0
    P = np.array(base_pts, float)
    for j in range(n):
        off = (j-(n-1)/2)*9; Q = []
        for i in range(len(P)):
            tt = P[min(i+1, len(P)-1)]-P[max(i-1, 0)]; tt /= (np.linalg.norm(tt)+1e-9)
            Q.append(tuple(P[i]+np.array([-tt[1], tt[0]])*off))
        trace(Q, 2.0, glow, pulse=glow > 0 and random.random() < 0.4)
# components
def rect(x0, y0, x1, y1, c, o=None): bd.rectangle((*tp(x0, y1), *tp(x1, y0)), fill=c, outline=o)
def smd(x, y, h):
    w, hh = (34, 16) if h else (16, 34)
    if not free(x-w/2, y-hh/2, x+w/2, y+hh/2): return
    occupied.append((x-w/2, y-hh/2, x+w/2, y+hh/2)); rect(x-w/2, y-hh/2, x+w/2, y+hh/2, (36, 27, 24))
    if h: rect(x-w/2, y-hh/2, x-w/2+8, y+hh/2, (165, 145, 130)); rect(x+w/2-8, y-hh/2, x+w/2, y+hh/2, (165, 145, 130))
    else: rect(x-w/2, y-hh/2, x+w/2, y-hh/2+8, (165, 145, 130)); rect(x-w/2, y+hh/2-8, x+w/2, y+hh/2, (165, 145, 130))
def qfp(x, y, s):
    if not free(x-s/2-12, y-s/2-12, x+s/2+12, y+s/2+12): return
    occupied.append((x-s/2-12, y-s/2-12, x+s/2+12, y+s/2+12)); n = int(s/9)
    for k in range(n):
        t = -s/2+s*(k+.5)/n
        for a in ((x+t, y+s/2, x+t, y+s/2+11), (x+t, y-s/2, x+t, y-s/2-11), (x+s/2, y+t, x+s/2+11, y+t), (x-s/2, y+t, x-s/2-11, y+t)):
            bd.line([tp(a[0], a[1]), tp(a[2], a[3])], fill=(155, 125, 105), width=max(1, int(2.4*TU)))
    rect(x-s/2, y-s/2, x+s/2, y+s/2, (22, 16, 15), (64, 40, 30))
    # glowing status LED on some chips
    if random.random() < 0.35:
        px, py = tp(x+s/2-10, y+s/2-10); r = 4*TU; ed.ellipse((px-r, py-r, px+r, py+r), fill=(255, 170, 80))
def bga(x, y, nx, ny):
    if not free(x, y, x+nx*14, y+ny*14): return
    occupied.append((x, y, x+nx*14, y+ny*14))
    for i in range(nx):
        for j in range(ny):
            px, py = tp(x+i*14+7, y+j*14+7); r = 4.2*TU
            bd.ellipse((px-r, py-r, px+r, py+r), fill=(118, 70, 42))
            if random.random() < 0.15: ed.ellipse((px-r, py-r, px+r, py+r), fill=(255, 150, 70))
for _ in range(1400):
    x, y = random.uniform(BX0+40, BX1-40), random.uniform(BY0+40, BY1-40); r = random.random()
    if r < .7: smd(x, y, random.random() < .5)
    elif r < .9: qfp(x, y, random.choice([48, 60, 80, 96, 120]))
    else: bga(x, y, random.randint(4, 9), random.randint(3, 7))
# HUD rings on the board around the chip
def ring(R, w, col, dash=None, ticks=0, tlen=0):
    n = 720
    for k in range(n):
        if dash and (k // dash) % 2: continue
        a0, a1 = 2*math.pi*k/n, 2*math.pi*(k+1)/n
        ed.line([tp(R*math.cos(a0), R*math.sin(a0)), tp(R*math.cos(a1), R*math.sin(a1))], fill=col, width=max(1, int(w*TU)))
    for k in range(ticks):
        a = 2*math.pi*k/ticks; L = tlen*(2 if k % 6 == 0 else 1)
        ed.line([tp(R*math.cos(a), R*math.sin(a)), tp((R+L)*math.cos(a), (R+L)*math.sin(a))], fill=col, width=max(1, int(w*TU)))
ring(255, 3.0, (255, 170, 80)); ring(272, 1.4, (200, 100, 40), dash=6)
ring(345, 2.0, (230, 120, 50), ticks=120, tlen=8)
ring(420, 4.0, (255, 140, 60), dash=40); ring(470, 1.2, (150, 60, 20), dash=3)
# arc segments (partial rings) for a HUD feel
for R, a0, a1, w in ((520, 0.2, 1.3, 5), (520, 3.4, 4.6, 5), (545, 1.9, 2.6, 2), (545, 5.0, 5.9, 2)):
    pts = [tp(R*math.cos(a), R*math.sin(a)) for a in np.linspace(a0, a1, 90)]
    ed.line(pts, fill=(255, 160, 70), width=int(w*TU))
# data pulses: bright comet segments travelling along glowing traces
for t in pulses:
    if random.random() < 0.5: continue
    i0 = random.randint(0, max(0, len(t)-8)); L = random.randint(4, 8)
    for j in range(L):
        if i0+j+1 >= len(t): break
        g = (j+1)/L
        ed.line([t[i0+j], t[i0+j+1]], fill=(255, int(170+80*g), int(90+150*g)), width=int(3.4*TU))
# chip light on the board
Bi = np.asarray(base, np.float32)
ys = (BY1 - np.arange(TH)/TU)[:, None]; xs = (np.arange(TW)/TU + BX0)[None, :]
illum = 1 + 3.4/(1 + (np.hypot(xs, ys)/340)**2)
Bi = np.clip(Bi*illum[..., None]*np.array([1.0, 0.78, 0.6]), 0, 255); base = Image.fromarray(Bi.astype(np.uint8)); del Bi, illum
# ---------------- warp ----------------
def H_of(src, dst):
    A, b = [], []
    for (u, v), (x, y) in zip(dst, src):
        A += [[u, v, 1, 0, 0, 0, -x*u, -x*v], [0, 0, 0, u, v, 1, -y*u, -y*v]]; b += [x, y]
    return tuple(np.linalg.solve(np.array(A, float), np.array(b, float)))
cb = [(BX0, BY1), (BX1, BY1), (BX1, BY0), (BX0, BY0)]
Hm = H_of([tp(*c) for c in cb], [proj(*c) for c in cb])
warp = lambda im: im.transform((SW, SH), Image.PERSPECTIVE, Hm, Image.BICUBIC)
board = warp(base); gboard = np.asarray(warp(emit), np.float32); del base, emit
# ---------------- 3D objects ----------------
sd = ImageDraw.Draw(board); hot = Image.new('RGB', (SW, SH)); hd = ImageDraw.Draw(hot)
def box(x0, y0, x1, y1, z0, z1, top, front, draw=None, hdraw=None, hfront=None):
    draw = draw or sd
    Tp = [proj(x0, y0, z1), proj(x1, y0, z1), proj(x1, y1, z1), proj(x0, y1, z1)]
    Fr = [proj(x0, y0, z0), proj(x1, y0, z0), proj(x1, y0, z1), proj(x0, y0, z1)]
    draw.polygon(Fr, fill=front); draw.polygon(Tp, fill=top)
    if hdraw and hfront: hdraw.polygon(Fr, fill=hfront)
    return Tp
caps = []
for _ in range(34):
    X, Y = random.uniform(-2000, 2000), random.uniform(-600, 2300)
    if math.hypot(X, Y) < 700: continue
    caps.append((X, Y, random.choice([26, 32, 40, 48]), random.choice([50, 70, 90, 120])))
for X, Y, R, Hh in sorted(caps, key=lambda c: -c[1]):
    n = 48; la = math.atan2(-Y, -X)
    top = [proj(X+R*math.cos(2*math.pi*k/n), Y+R*math.sin(2*math.pi*k/n), Hh) for k in range(n)]
    bot = [proj(X+R*math.cos(2*math.pi*k/n), Y+R*math.sin(2*math.pi*k/n), 0) for k in range(n)]
    for k in range(n):
        a = 2*math.pi*(k+.5)/n
        if math.sin(a) > 0.15: continue
        s_ = max(0, math.cos(a-la))**3; v = 0.5+0.5*math.cos(a+0.6)      # rim light from the chip + soft fill
        sd.polygon([bot[k], bot[(k+1) % n], top[(k+1) % n], top[k]], fill=(int(28+22*v+190*s_), int(20+14*v+110*s_), int(18+10*v+55*s_)))
    sd.polygon(top, fill=(48, 36, 32), outline=(150, 110, 85))
    ins = [proj(X+R*0.6*math.cos(2*math.pi*k/n), Y+R*0.6*math.sin(2*math.pi*k/n), Hh) for k in range(n)]
    sd.line(ins+[ins[0]], fill=(80, 60, 50), width=2)
    # glowing ring on top (futuristic capacitor cap)
    hd.line(top+[top[0]], fill=(255, 140, 50), width=3)
# chip: pins, substrate, glowing lid
pins = 24
for side in range(4):
    for k in range(pins):
        t = -PKG+10+(2*PKG-20)*k/(pins-1)
        a, b2 = [((t, -PKG), (t, -PKG-18)), ((t, PKG), (t, PKG+18)), ((-PKG, t), (-PKG-18, t)), ((PKG, t), (PKG+18, t))][side]
        sd.line([proj(*a, 4), proj(*b2, 2)], fill=(240, 195, 150), width=4); hd.line([proj(*a, 4), proj(*b2, 2)], fill=(140, 70, 25), width=4)
box(-PKG, -PKG, PKG, PKG, 0, 20, (46, 26, 20), (95, 46, 24))
box(-PKG+10, -PKG+10, PKG-10, PKG-10, 20, 27, (66, 36, 26), (170, 80, 30), hdraw=hd, hfront=(120, 50, 15))
L = 128
lid = box(-L, -L, L, L, 27, 56, (255, 235, 200), (255, 150, 60), hdraw=hd, hfront=(255, 110, 30))
lm = Image.new('L', (SW, SH)); ImageDraw.Draw(lm).polygon(lid, fill=255); lm = np.asarray(lm, np.float32)/255
cxp, cyp = proj(0, 0, 56)
gy, gx = np.mgrid[0:SH, 0:SW].astype(np.float32)
sx = F*L/D*1.15; sy = F*L/D*0.75
rad = np.clip(np.hypot((gx-cxp)/sx, (gy-cyp)/sy), 0, 1)
bo = np.asarray(board, np.float32)
lidc = np.dstack([np.full_like(rad, 252), 240-100*rad**1.3, 220-160*rad**1.3])
bo = bo*(1-lm[..., None]) + lidc*lm[..., None]
board = Image.fromarray(bo.astype(np.uint8)); sd = ImageDraw.Draw(board); del bo, lidc
# circuitry etched on the lid + glowing core
for k in range(1, 10):
    t = -L+2*L*k/10
    sd.line([proj(t, -L+12, 56), proj(t, L-12, 56)], fill=(255, 200, 140), width=1)
    sd.line([proj(-L+12, t, 56), proj(L-12, t, 56)], fill=(255, 200, 140), width=1)
core = [proj(-46, -46, 56), proj(46, -46, 56), proj(46, 46, 56), proj(-46, 46, 56)]
sd.polygon(core, outline=(255, 250, 235), width=3); hd.polygon(core, fill=(255, 210, 150))
sd.line(lid+[lid[0]], fill=(255, 250, 240), width=5); hd.line(lid+[lid[0]], fill=(255, 200, 120), width=6)
# floating holographic rings above the chip
def ring3d(R, Z, w, col, segs=None):
    n = 360
    pts = [proj(R*math.cos(2*math.pi*k/n), R*math.sin(2*math.pi*k/n), Z) for k in range(n+1)]
    for k in range(n):
        if segs and not any(a <= k < b for a, b in segs): continue
        hd.line([pts[k], pts[k+1]], fill=col, width=w)
ring3d(230, 150, 4, (255, 170, 80), segs=[(0, 70), (95, 160), (185, 250), (275, 340)])
ring3d(205, 175, 2, (255, 210, 140))
ring3d(300, 120, 3, (230, 110, 40), segs=[(20, 60), (120, 200), (250, 300)])
ring3d(160, 260, 3, (255, 190, 110), segs=[(0, 120), (180, 300)])
# vertical connector lines from board ring up to floating ring
for k in range(0, 360, 30):
    a = math.radians(k)
    hd.line([proj(230*math.cos(a), 230*math.sin(a), 56), proj(230*math.cos(a), 230*math.sin(a), 150)], fill=(150, 70, 25), width=2)
# light pillar and beams
beams = Image.new('RGB', (SW, SH)); bw = ImageDraw.Draw(beams)
x_l, x_r = proj(-L, -L, 56)[0], proj(L, -L, 56)[0]; y_base = cyp
for x in range(int(x_l), int(x_r)):
    u = (x - (x_l+x_r)/2)/((x_r-x_l)/2); inten = max(0, 1-u*u)**1.5
    for seg in range(40):
        f0, f1 = seg/40, (seg+1)/40; a = inten*(1-f0)**2.2*0.22
        bw.line([(x, y_base-y_base*f0), (x, y_base-y_base*f1)], fill=(int(255*a), int(190*a), int(120*a)))
for _ in range(90):
    X, Y = random.uniform(-L, L), random.uniform(-L, L); x0, y0 = proj(X, Y, 56); h_ = random.uniform(0.3, 1.0)*y0
    w_ = random.choice([1, 2, 2, 3, 4]); g0 = random.uniform(0.5, 1.0)
    for seg in range(30):
        f0, f1 = seg/30, (seg+1)/30; a = g0*(1-f0)**1.7
        bw.line([(x0, y0-h_*f0), (x0, y0-h_*f1)], fill=(int(255*a), int(200*a), int(140*a)), width=w_)
for _ in range(70):
    X, Y = random.uniform(-1400, 1400), random.uniform(-300, 1600)
    if max(abs(X), abs(Y)) < 300: continue
    x0, y0 = proj(X, Y, 0); h_ = random.uniform(60, 420)*F/depth(X, Y)
    for seg in range(14):
        f0, f1 = seg/14, (seg+1)/14; a = (1-f0)**2*0.7
        bw.line([(x0, y0-h_*f0), (x0, y0-h_*f1)], fill=(int(255*a), int(140*a), int(60*a)), width=2)
# floating particles (bokeh) near the chip
parts = Image.new('RGB', (SW, SH)); pw = ImageDraw.Draw(parts)
for _ in range(420):
    X, Y, Z = rng.normal(0, 520), rng.normal(250, 600), abs(rng.normal(0, 260))
    if depth(X, Y, Z) < 400: continue
    x, y = proj(X, Y, Z); r = random.uniform(1.5, 5.5)*1900/depth(X, Y, Z); a = random.uniform(0.3, 1.0)
    pw.ellipse((x-r, y-r, x+r, y+r), fill=(int(255*a), int(185*a), int(110*a)))
# ---------------- compositing ----------------
dark = np.asarray(board, np.float32)
E = np.asarray(hot, np.float32) + gboard
Ei = Image.fromarray(np.clip(E, 0, 255).astype(np.uint8))
dark += E*0.9
for r_, k_ in ((3, 0.9), (12, 1.0), (40, 1.2), (110, 0.9)):
    dark += np.asarray(Ei.filter(ImageFilter.GaussianBlur(r_)), np.float32)*k_
Bm = np.asarray(beams, np.float32); dark += Bm*1.6 + np.asarray(beams.filter(ImageFilter.GaussianBlur(8)), np.float32)*2.0
Pm = np.asarray(parts, np.float32); dark += Pm*0.8 + np.asarray(parts.filter(ImageFilter.GaussianBlur(6)), np.float32)*1.6
# chip halo + anamorphic flare
rr = np.hypot((gx-cxp)/900, (gy-cyp)/480); g = np.exp(-rr**2*2.0)
dark += np.dstack([255*g, 135*g, 55*g])*0.6
fl = np.exp(-((gy-cyp)/7)**2)*np.exp(-np.abs(gx-cxp)/1300); fl2 = np.exp(-((gy-cyp)/28)**2)*np.exp(-np.abs(gx-cxp)/700)
dark += np.dstack([255*(fl+0.5*fl2), 200*(fl+0.4*fl2), 150*fl+40*fl2])*0.9
# atmospheric fog towards the horizon
far = np.clip((CY*0.92 - gy)/ (CY*0.92), 0, 1)
dark = dark*(1-0.55*far[..., None]) + np.array([60, 22, 10])*0.55*far[..., None]
# tone map + colour grade (deep red shadows, golden highlights)
dark = 255*(1-np.exp(-dark/175.0))
lum = dark.mean(2, keepdims=True)/255
dark = dark*(0.88+0.12*lum) + np.array([10, 0, 2])*(1-lum)
vig = np.clip(1 - 0.55*np.hypot((gx-SW/2)/(SW*0.62), (gy-SH*0.45)/(SH*0.75))**2.4, 0.25, 1)
dark *= vig[..., None]
img = Image.fromarray(np.clip(dark, 0, 255).astype(np.uint8))
# depth of field: soften the far horizon and the very near foreground
blur = img.filter(ImageFilter.GaussianBlur(3.2))
m = np.clip(np.maximum((CY*0.8-gy)/(CY*0.6), (gy-SH*0.86)/(SH*0.14)), 0, 1)
img = Image.composite(blur, img, Image.fromarray((m*255).astype(np.uint8)))
img.save(OUT+'EPTC2026_glowing_chip_futuristic_3840x2160.png', optimize=True)
img.resize((1920, 1080), Image.LANCZOS).save(OUT+'preview.png')
print('ok')
