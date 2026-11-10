# Original procedural artwork: holographic wireframe hands presenting a floating chip in a circuit corona.
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
random.seed(21); rng = np.random.default_rng(21)
W, H = 3840, 2160; OUT = 'v6/'
Dc, f = 2000.0, 2600.0
def P(v):                                    # world (X right, Y up, Z to viewer) -> screen px
    X, Y, Z = v; w = Dc - Z
    return (W/2 + f*X/w, H/2 - f*Y/w)
CAM = np.array([0, 0, Dc])
def norm(v): v = np.asarray(v, float); return v/np.linalg.norm(v)

class Layer:                                  # additive float layer drawn through PIL in chunks
    def __init__(s): s.acc = np.zeros((H, W, 3), np.float32); s.im = Image.new('RGB', (W, H)); s.d = ImageDraw.Draw(s.im); s.n = 0
    def tick(s):
        s.n += 1
        if s.n >= 400: s.flush()
    def flush(s):
        s.acc += np.asarray(s.im, np.float32); s.im = Image.new('RGB', (W, H)); s.d = ImageDraw.Draw(s.im); s.n = 0
    def line(s, a, b, col, w=2): s.d.line([a, b], fill=tuple(int(c) for c in col), width=w); s.tick()
    def dot(s, p, r, col): s.d.ellipse((p[0]-r, p[1]-r, p[0]+r, p[1]+r), fill=tuple(int(c) for c in col)); s.tick()
    def get(s): s.flush(); return s.acc

AMBER = np.array([255, 170, 80]); GOLD = np.array([255, 205, 130]); ORNG = np.array([255, 120, 40]); RUSTc = np.array([190, 60, 20])

# ======================= background =======================
gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot((gx-W/2)/(W*0.55), (gy-H/2)/(H*0.6))
bg = np.dstack([40+70*np.exp(-r**2*1.6), 10+22*np.exp(-r**2*1.6), 8+10*np.exp(-r**2*1.6)])*np.clip(1.15-0.45*r, 0.3, 1)[..., None]
streams = Layer()
for _ in range(170):                         # horizontal data streams, from both edges towards the centre
    y = rng.normal(H/2, H*0.26); side = random.choice([-1, 1])
    x0 = 0 if side < 0 else W; L = random.uniform(500, 1500); x1 = x0 - side*L
    a = random.uniform(0.15, 0.6); col = random.choice([AMBER, ORNG, GOLD])*a
    n = 30
    for k in range(n):                       # fade toward the centre
        t0, t1 = k/n, (k+1)/n; g = (1-t0)**1.2
        streams.line((x0+(x1-x0)*t0, y), (x0+(x1-x0)*t1, y), col*g, w=random.choice([1, 2, 2, 3]))
    for _ in range(random.randint(0, 3)):
        t = random.random(); streams.dot((x0+(x1-x0)*t, y), random.uniform(3, 7), GOLD*a*(1-t))
    if random.random() < 0.4:                # dashed companion line
        for k in range(0, 40, 2):
            t0, t1 = k/40, (k+1)/40; streams.line((x0+(x1-x0)*t0, y+8), (x0+(x1-x0)*t1, y+8), col*0.5*(1-t0), w=1)

# ======================= circuit corona behind the chip =======================
corona = Layer(); CZ = -260
def ang_env(a):                               # organic outline of the cloud
    return 1 + 0.18*math.sin(3*a+0.7) + 0.12*math.sin(5*a+2.1) + 0.07*math.sin(9*a)
for i in range(520):
    a = random.uniform(0, 2*math.pi); R0 = random.uniform(190, 260)
    x, y = R0*math.cos(a), R0*math.sin(a)
    Rmax = random.uniform(420, 820)*ang_env(a)
    d = (round(math.cos(a)), round(math.sin(a)))
    if d == (0, 0): d = (1, 0)
    pts = [(x, y)]; step = 14
    for k in range(80):
        rad_dir = norm((x, y))
        cand = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        if random.random() < 0.18 or k == 0:
            d = max(cand, key=lambda c: (c[0]*rad_dir[0]+c[1]*rad_dir[1])/math.hypot(*c) + random.uniform(-0.45, 0.45))
        x += d[0]*step; y += d[1]*step; pts.append((x, y))
        if math.hypot(x, y) > Rmax: break
    rr = math.hypot(x, y); g0 = random.uniform(0.35, 1.0)
    for p0, p1 in zip(pts, pts[1:]):
        fall = math.exp(-(math.hypot(*p0)-200)/420)
        corona.line(P((p0[0], p0[1], CZ)), P((p1[0], p1[1], CZ)), AMBER*g0*fall, w=2)
    if random.random() < 0.7:
        corona.dot(P((x, y, CZ)), random.uniform(4, 9), GOLD*g0*math.exp(-(rr-200)/600))
# concentric HUD rings in the corona
for R, wdt, seg in ((300, 3, 1), (340, 2, 3), (560, 2, 7), (600, 4, 0)):
    n = 720
    for k in range(n):
        if seg and (k // (seg*6)) % 2: continue
        if seg == 0 and (k % 180) > 110: continue
        a0, a1 = 2*math.pi*k/n, 2*math.pi*(k+1)/n
        corona.line(P((R*math.cos(a0), R*math.sin(a0), CZ)), P((R*math.cos(a1), R*math.sin(a1), CZ)), ORNG*0.8, w=wdt)
# particles / bokeh
parts = Layer()
for _ in range(2600):
    rr = abs(rng.normal(0, 430)); a = random.uniform(0, 2*math.pi)
    v = (rr*math.cos(a)*1.25, rr*math.sin(a), rng.normal(-100, 250))
    s = P(v); sz = random.choice([1.5, 2, 2.5, 3, 4, 6, 9]) * (1 if random.random() < 0.9 else 2)
    parts.dot(s, sz, (GOLD if random.random() < 0.6 else AMBER)*random.uniform(0.25, 1.0))

# ======================= floating chip =======================
def rotm(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
R_chip = rotm(math.radians(-38), math.radians(18), math.radians(28))
def C(x, y, z): return P(R_chip @ np.array([x, y, z]))
chip_im = Image.new('RGBA', (W, H)); cd = ImageDraw.Draw(chip_im)
chipglow = Layer()
Hs, th = 175, 34
def face(pts, fill, outline=None, w=0): cd.polygon([C(*p) for p in pts], fill=fill, outline=outline, width=w)
# pins (gull-wing) on all sides, drawn first (behind body edges where hidden)
npins = 26
for side in range(4):
    for k in range(npins):
        t = -Hs+12+(2*Hs-24)*k/(npins-1)
        if side == 0: a, b, c = (t, -Hs, 0), (t, -Hs-22, -6), (t, -Hs-34, -14)
        elif side == 1: a, b, c = (t, Hs, 0), (t, Hs+22, -6), (t, Hs+34, -14)
        elif side == 2: a, b, c = (-Hs, t, 0), (-Hs-22, t, -6), (-Hs-34, t, -14)
        else: a, b, c = (Hs, t, 0), (Hs+22, t, -6), (Hs+34, t, -14)
        cd.line([C(*a), C(*b), C(*c)], fill=(240, 190, 120, 255), width=5)
        chipglow.line(C(*b), C(*c), GOLD*0.5, w=4)
# body: bottom/sides then top (camera sees the top, z+)
top = [(-Hs, -Hs, th), (Hs, -Hs, th), (Hs, Hs, th), (-Hs, Hs, th)]
for (p, q) in (((-Hs, -Hs), (Hs, -Hs)), ((Hs, -Hs), (Hs, Hs)), ((Hs, Hs), (-Hs, Hs)), ((-Hs, Hs), (-Hs, -Hs))):
    poly = [(p[0], p[1], 0), (q[0], q[1], 0), (q[0], q[1], th), (p[0], p[1], th)]
    nrm = R_chip @ np.array([(p[1]+q[1])/2, -(p[0]+q[0])/2, 0])*-1
    lit = max(0.15, (R_chip @ norm([(p[0]+q[0])/2, (p[1]+q[1])/2, 0]))[2])
    face(poly, (int(70+120*lit), int(30+55*lit), int(18+25*lit), 255))
face(top, (34, 16, 12, 255))
# die window + etched circuitry on the top
d0 = 105
face([(-d0, -d0, th+1), (d0, -d0, th+1), (d0, d0, th+1), (-d0, d0, th+1)], (60, 26, 14, 255), (255, 170, 80, 255), 3)
for k in range(1, 14):
    t = -d0+2*d0*k/14
    cd.line([C(t, -d0+6, th+1.5), C(t, d0-6, th+1.5)], fill=(150, 70, 30, 255), width=2)
    cd.line([C(-d0+6, t, th+1.5), C(d0-6, t, th+1.5)], fill=(150, 70, 30, 255), width=2)
# BGA-like dot ring between die and edge
for i in range(-7, 8):
    for (x, y) in ((i*20, -140), (i*20, 140), (-140, i*20), (140, i*20)):
        p = C(x, y, th+1); cd.ellipse((p[0]-4, p[1]-4, p[0]+4, p[1]+4), fill=(230, 160, 90, 255))
core = [(-40, -40, th+2), (40, -40, th+2), (40, 40, th+2), (-40, 40, th+2)]
face(core, (255, 220, 160, 255))
for poly, g in ((top, 1.0), (core, 1.0)):
    pts = [C(*p) for p in poly]
    for a, b in zip(pts, pts[1:]+pts[:1]): chipglow.line(a, b, GOLD*g, w=5)
cpts = [C(*p) for p in core]; chipglow.d.polygon(cpts, fill=(255, 200, 130))

# ======================= wireframe hands =======================
def finger_chain(base, direction, curl_axis, lengths, radii, curls, spread_rot=None):
    """returns centreline points and radii along a jointed finger"""
    pts, rad = [], []; p = np.array(base, float); d = norm(direction)
    for seg, (L, r0, r1, cang) in enumerate(zip(lengths, radii[:-1], radii[1:], curls)):
        # rotate direction about curl axis (bend toward the palm)
        k = norm(curl_axis); c, s = math.cos(cang), math.sin(cang)
        d = d*c + np.cross(k, d)*s + k*np.dot(k, d)*(1-c)
        n = 6
        for i in range(n + (1 if seg == len(lengths)-1 else 0)):
            t = i/n; pts.append(p + d*L*t); rad.append(r0+(r1-r0)*t)
        p = p + d*L
    return np.array(pts), np.array(rad)
def tube(pts, rad, sides, flat=None):
    """ring vertices around a centreline; flat=(ratio array) squashes along local z"""
    rings, nrms = [], []
    for i in range(len(pts)):
        t = pts[min(i+1, len(pts)-1)] - pts[max(i-1, 0)]; t = norm(t)
        a = norm(np.cross(t, [0, 0, 1])) if abs(t[2]) < 0.95 else norm(np.cross(t, [1, 0, 0]))
        b = np.cross(t, a)
        ring, nr = [], []
        for k in range(sides):
            th_ = 2*math.pi*k/sides
            ca, sa = math.cos(th_), math.sin(th_)
            if flat is not None:
                e = 0.5; ca2 = math.copysign(abs(ca)**e, ca); sa2 = math.copysign(abs(sa)**e, sa)
                off = a*ca2*rad[i] + b*sa2*rad[i]*flat[i]
            else:
                off = a*ca*rad[i] + b*sa*rad[i]
            ring.append(pts[i]+off); nr.append(norm(a*ca + b*sa))
        rings.append(ring); nrms.append(nr)
    return rings, nrms
def cap(pts, rad, fl=None, n=5):
    pts = list(pts); rad = list(rad); fl = None if fl is None else list(fl)
    t = norm(pts[-1]-pts[-2]); r_end = rad[-1]
    for j in range(1, n+1):
        a = j*math.pi/2/(n+0.35)
        pts.append(pts[-1-(j-1)] + t*0 if False else pts[len(pts)-j] + t*0)  # placeholder (replaced below)
    return None
def capped(pts, rad, fl=None, n=5):
    pts = [np.asarray(p, float) for p in pts]; rad = list(rad); fl = None if fl is None else list(fl)
    t = norm(pts[-1]-pts[-2]); P0 = pts[-1]; r_end = rad[-1]; f_end = fl[-1] if fl is not None else None
    for j in range(1, n+1):
        a = j*math.pi/2/(n+0.4)
        pts.append(P0 + t*r_end*math.sin(a)); rad.append(max(0.6, r_end*math.cos(a)))
        if fl is not None: fl.append(f_end)
    return np.array(pts), np.array(rad), (None if fl is None else np.array(fl))
def build_hand():
    parts = []
    # ---- forearm -> bent wrist -> palm, one continuous tube (palm faces +z, fingers +y, thumb +x)
    b = math.radians(58); fd = np.array([0, -math.cos(b), -math.sin(b)])          # forearm bends back behind the palm
    Wr = np.array([0, -10, 0])
    arm = [Wr + fd*sv for sv in np.linspace(560, 70, 11)]
    A, B = Wr + fd*70, np.array([0, 28, 0])
    bez = [(1-t)**2*A + 2*(1-t)*t*Wr + t*t*B for t in np.linspace(0, 1, 8)[1:]]
    palm = [np.array([0, y, 0]) for y in np.linspace(28, 90, 7)[1:]]
    cen = np.array(arm + bez + palm)
    n_arm, n_bez, n_palm = len(arm), len(bez), len(palm)
    w = np.concatenate([np.linspace(38, 31, n_arm), np.linspace(30, 37, n_bez), np.linspace(38, 42, n_palm)])
    fl = np.concatenate([np.linspace(0.78, 0.7, n_arm), np.linspace(0.62, 0.42, n_bez), np.linspace(0.38, 0.32, n_palm)])
    cen, w, fl = capped(cen, w, fl, n=4)
    parts.append(tube(cen, w, 24, flat=fl))
    # ---- fingers on a knuckle arc, slim, curling gently toward the palm (+z)
    fingers = [(30, 80, 8.6, 0.17, 94), (10, 86, 9.2, 0.04, 104), (-10, 83, 8.8, -0.09, 97), (-29, 76, 7.6, -0.23, 77)]
    for x, yb, r0, spread, L in fingers:
        d = norm([math.sin(spread), math.cos(spread), 0])
        pts, rad = finger_chain([x, yb, 1.5], d, [1, 0, 0], [L*0.46, L*0.30, L*0.24], [r0, r0*0.90, r0*0.80, r0*0.58],
                                [math.radians(6), math.radians(16), math.radians(14)])
        # small bulges at the knuckles
        k = np.arange(len(rad)); rad = rad*(1 + 0.07*np.exp(-((k % 6))**2/1.2)*(k > 0))
        pts, rad, _ = capped(pts, rad, n=5)
        parts.append(tube(pts, rad, 12))
    # ---- thumb: out from the base of the palm, then up alongside the fingers
    d0 = norm([0.40, 0.62, 0.68]); kax = norm(np.cross(d0, [0, 1, 0]))
    pts, rad = finger_chain([28, 10, 9], d0, kax, [42, 32, 28], [15, 12.5, 10.5, 7.4],
                            [0, math.radians(22), math.radians(16)])
    pts, rad, _ = capped(pts, rad, n=5)
    parts.append(tube(pts, rad, 14))
    return parts
def place(parts, origin, fdir, pnorm, scale, mirror=False):
    y = norm(fdir); z = norm(np.array(pnorm) - np.dot(pnorm, y)*y); x = np.cross(y, z)
    if mirror: x = -x
    M = np.stack([x, y, z], 1)
    out = []
    for rings, nrms in parts:
        out.append(([[origin + M @ (np.array(v)*scale) for v in ring] for ring in rings],
                    [[M @ n for n in nr] for nr in nrms]))
    return out
handL = Layer(); handDots = Layer()
def draw_hand(parts):
    for rings, nrms in parts:
        nR, nS = len(rings), len(rings[0])
        S = [[P(v) for v in ring] for ring in rings]
        B = np.zeros((nR, nS))
        for i in range(nR):
            for k in range(nS):
                v = rings[i][k]; n = nrms[i][k]; view = norm(CAM - v)
                fac = np.dot(n, view)
                b = 0.32 + 0.68*(1-abs(fac))**1.4          # fresnel: silhouette glows brightest
                if fac < 0: b *= 0.35                         # far side dimmer (hologram transparency)
                B[i, k] = b
        for i in range(nR):
            for k in range(nS):
                b = B[i, k]
                handL.line(S[i][k], S[i][(k+1) % nS], np.array([255, 228, 185])*0.85*(b+B[i, (k+1) % nS])/2, w=2)   # rings
                if i+1 < nR: handL.line(S[i][k], S[i+1][k], AMBER*0.9*(b+B[i+1, k])/2, w=2)     # longitudinal
                if i+1 < nR: handL.line(S[i][k], S[i+1][(k+1) % nS], GOLD*0.5*b, w=1)  # diagonal (triangulated mesh)
                if b > 0.75 and random.random() < 0.25: handDots.dot(S[i][k], random.uniform(2.5, 5), GOLD*b)
hand = build_hand()
draw_hand(place(hand, np.array([-800, -330, 120]), [0.22, 1.0, 0.0], [1.0, -0.12, 0.42], 3.4, mirror=True))
draw_hand(place(hand, np.array([800, -330, 120]), [-0.22, 1.0, 0.0], [-1.0, -0.12, 0.42], 3.4))

# ======================= compositing =======================
img = bg.copy()
def addglow(arr, k0, blurs):
    global img
    im8 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); img += arr*k0
    for rad_, k in blurs: img += np.asarray(im8.filter(ImageFilter.GaussianBlur(rad_)), np.float32)*k
addglow(streams.get(), 0.8, [(4, 0.8), (18, 0.6)])
addglow(corona.get(), 0.9, [(3, 0.9), (14, 1.0), (50, 1.3)])
addglow(parts.get(), 0.9, [(5, 1.2), (20, 0.6)])
# big core light behind the chip
cr = np.hypot((gx-W/2)/700, (gy-H/2)/560); img += np.dstack([255*np.exp(-cr**2*2), 140*np.exp(-cr**2*2), 60*np.exp(-cr**2*2)])*0.75
# chip (opaque) + its glow
ch = np.asarray(chip_im, np.float32); a = ch[..., 3:4]/255
img = img*(1-a*0.97) + ch[..., :3]*a
addglow(chipglow.get(), 0.9, [(3, 1.0), (16, 1.0), (60, 0.9)])
addglow(handL.get(), 1.35, [(3, 1.2), (12, 1.1), (40, 0.8)])
addglow(handDots.get(), 1.0, [(4, 1.2), (14, 0.6)])
img = 255*(1-np.exp(-img/170.0))                     # tone map
vig = np.clip(1-0.5*np.hypot((gx-W/2)/(W*0.6), (gy-H/2)/(H*0.7))**2.6, 0.3, 1); img *= vig[..., None]
out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
out.save(OUT+'EPTC2026_holo_hands_chip_v2_3840x2160.png', optimize=True)
out.resize((1920, 1080), Image.LANCZOS).save(OUT+'preview.png'); print('ok')
