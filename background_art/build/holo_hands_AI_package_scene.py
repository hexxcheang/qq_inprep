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

# ======================= floating AI accelerator package (GPU die + 4 HBM stacks) =======================
from PIL import ImageFont
def rotm(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]); Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx
R_chip = rotm(math.radians(-38), math.radians(18), math.radians(28))
def Wd(x, y, z): return R_chip @ np.array([x, y, z], float)
def C(x, y, z): return P(Wd(x, y, z))
chip_im = Image.new('RGBA', (W, H)); cd = ImageDraw.Draw(chip_im)
chipglow = Layer()
LIGHT = norm([0.2, 0.6, 1.0])
def shade(base, n_w, amb=0.38):
    k = amb + (1-amb)*max(0.0, float(np.dot(n_w, LIGHT)))
    return tuple(int(min(255, c*k)) for c in base)
FACES = [((0, 0, 1), (4, 5, 6, 7)), ((0, 0, -1), (0, 3, 2, 1)), ((0, -1, 0), (0, 1, 5, 4)),
         ((1, 0, 0), (1, 2, 6, 5)), ((0, 1, 0), (2, 3, 7, 6)), ((-1, 0, 0), (3, 0, 4, 7))]
boxes = []        # (depth, draw-callable)
def add_box(x0, y0, x1, y1, z0, z1, col, top_col=None, edge=None, glow_edges=None, top_hook=None, side_hook=None, near_only=False):
    V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    centre = Wd((x0+x1)/2, (y0+y1)/2, (z0+z1)/2)
    def draw():
        for n, idx in FACES:
            n_w = R_chip @ np.array(n, float)
            fc = Wd(*np.mean([V[i] for i in idx], 0))
            if np.dot(n_w, CAM - fc) <= 0: continue
            pts = [C(*V[i]) for i in idx]
            c = shade(top_col if (n == (0, 0, 1) and top_col) else col, n_w)
            cd.polygon(pts, fill=c+(255,), outline=edge)
            if n == (0, 0, 1) and top_hook: top_hook([V[i] for i in idx])
            if n[2] == 0 and side_hook: side_hook(n, [V[i] for i in idx])
            if glow_edges is not None:
                vs = [V[i] for i in idx]
                for (va, vb), (a, b) in zip(zip(vs, vs[1:]+vs[:1]), zip(pts, pts[1:]+pts[:1])):
                    if near_only and (Wd(*va)[2] < centre[2] - 1 or Wd(*vb)[2] < centre[2] - 1): continue   # skip far edges (would glow through)
                    chipglow.line(a, b, glow_edges, w=3)
    boxes.append((centre[2], draw))
# -- substrate + BGA pad dots + stiffener frame
S0 = 245
add_box(-S0, -S0, S0, S0, 0, 16, (60, 28, 16), top_col=(30, 16, 12), glow_edges=AMBER*0.55, near_only=True)
def frame_hook(face):
    pass
FR, FW, FH = 232, 22, 34                       # stiffener ring (metal frame)
NSEG = 12                                       # short segments so far/near ordering is correct
for (x0, y0, x1, y1) in ((-FR, -FR, FR, -FR+FW), (-FR, FR-FW, FR, FR), (-FR, -FR+FW, -FR+FW, FR-FW), (FR-FW, -FR+FW, FR, FR-FW)):
    horiz = (x1-x0) > (y1-y0)
    for k in range(NSEG):
        if horiz: a, b = x0+(x1-x0)*k/NSEG, x0+(x1-x0)*(k+1)/NSEG; add_box(a, y0, b, y1, 16, FH, (120, 92, 76), top_col=(150, 118, 96))
        else:     a, b = y0+(y1-y0)*k/NSEG, y0+(y1-y0)*(k+1)/NSEG; add_box(x0, a, x1, b, 16, FH, (120, 92, 76), top_col=(150, 118, 96))
# -- silicon interposer
add_box(-195, -195, 195, 195, 16, 24, (80, 36, 18), top_col=(34, 18, 14))
# -- central AI GPU die (with glowing label + etched grid)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def label_on(face, lines, scale=1.0, col=(255, 205, 120)):
    """draw text onto a top face quad (perspective-correct) into chip image and glow layer"""
    tw, th = 600, 600
    t = Image.new('L', (tw, th)); td = ImageDraw.Draw(t)
    y = th*0.5 - sum(sz for _, sz in lines)*scale*0.6
    for txt, sz in lines:
        fnt = ImageFont.truetype(FONT, int(sz*scale)); bb = td.textbbox((0, 0), txt, font=fnt)
        td.text(((tw-(bb[2]-bb[0]))/2-bb[0], y-bb[1]), txt, fill=255, font=fnt); y += (bb[3]-bb[1]) + sz*scale*0.28
    dst = [C(*v) for v in face]                # face corners in order (x0,y0),(x1,y0),(x1,y1),(x0,y1)
    # texture rows run +y downward on screen, so map texture corners to (x0,y1),(x1,y1),(x1,y0),(x0,y0)
    q = [dst[3], dst[2], dst[1], dst[0]]
    A, bvec = [], []
    for (u, v), (xx, yy) in zip(q, [(0, 0), (tw, 0), (tw, th), (0, th)]):
        A += [[u, v, 1, 0, 0, 0, -xx*u, -xx*v], [0, 0, 0, u, v, 1, -yy*u, -yy*v]]; bvec += [xx, yy]
    coef = np.linalg.solve(np.array(A, float), np.array(bvec, float))
    m = t.transform((W, H), Image.PERSPECTIVE, tuple(coef), Image.BICUBIC)
    solid = Image.new('RGBA', (W, H), col+(255,)); chip_im.paste(solid, (0, 0), m)
    chipglow.im.paste(Image.new('RGB', (W, H), tuple(int(c*0.55) for c in col)), (0, 0), m); chipglow.tick()
def gpu_top(face):
    xs = [v[0] for v in face]; ys = [v[1] for v in face]; z = face[0][2]+0.5
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for k in range(1, 12):                     # faint etched grid
        t = x0+(x1-x0)*k/12; cd.line([C(t, y0+6, z), C(t, y1-6, z)], fill=(95, 50, 28, 255), width=1)
        t = y0+(y1-y0)*k/12; cd.line([C(x0+6, t, z), C(x1-6, t, z)], fill=(95, 50, 28, 255), width=1)
    inner = [(x0+10, y0+10, z), (x1-10, y0+10, z), (x1-10, y1-10, z), (x0+10, y1-10, z)]
    pts = [C(*v) for v in inner]
    for a, b in zip(pts, pts[1:]+pts[:1]): chipglow.line(a, b, GOLD*0.9, w=4)
    label_on([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [('AI', 210), ('GPU', 92)], col=(255, 214, 140))
add_box(-82, -82, 82, 82, 24, 46, (60, 30, 18), top_col=(26, 16, 14), glow_edges=GOLD*0.8, top_hook=gpu_top)
# -- four HBM stacks: 8 thin dies each, with glowing seams
HB, HS = 64, 150                                # half-size, centre offset
def hbm(cx, cy):
    z = 24; layers = 8; th_ = 9.0
    for k in range(layers):
        top = (k == layers-1)
        def seam(n, face, k=k):               # glowing line along the top edge of each layer's side face
            hi = [v for v in face if v[2] == max(w[2] for w in face)]
            if len(hi) == 2: chipglow.line(C(*hi[0]), C(*hi[1]), np.array([255, 160, 60])*(0.75 if k < layers-1 else 0.5), w=4)
            lo = [v for v in face if v[2] == min(w[2] for w in face)]
            # small glowing TSV dots on the side face
            for t in np.linspace(0.12, 0.88, 7):
                p = np.array(lo[0])*(1-t) + np.array(lo[1])*t; p[2] += th_*0.5
                chipglow.dot(C(*p), 2.6, np.array([255, 190, 110])*0.8)
        add_box(cx-HB, cy-HB, cx+HB, cy+HB, z, z+th_-1.6, (78, 46, 28), top_col=(30, 20, 16) if top else (60, 34, 22),
                side_hook=seam, top_hook=(lambda face: label_on(face, [('HBM', 120), ('STACK', 62)], col=(255, 200, 120))) if top else None,
                glow_edges=GOLD*0.55 if top else None)
        z += th_
for cx, cy in ((-HS, -HS), (HS, -HS), (-HS, HS), (HS, HS)): hbm(cx, cy)
# -- paint far -> near
for _, fn in sorted(boxes, key=lambda b: b[0]): fn()
# soft glow beneath the package (light from the interposer)


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
cr = np.hypot((gx-W/2)/700, (gy-H/2)/560); img += np.dstack([255*np.exp(-cr**2*2), 140*np.exp(-cr**2*2), 60*np.exp(-cr**2*2)])*0.45
# chip (opaque) + its glow
ch = np.asarray(chip_im, np.float32); a = ch[..., 3:4]/255
img = img*(1-a) + ch[..., :3]*a
addglow(chipglow.get(), 0.9, [(3, 0.9), (16, 0.6), (60, 0.35)])
addglow(handL.get(), 1.35, [(3, 1.2), (12, 1.1), (40, 0.8)])
addglow(handDots.get(), 1.0, [(4, 1.2), (14, 0.6)])
img = 255*(1-np.exp(-img/170.0))                     # tone map
vig = np.clip(1-0.5*np.hypot((gx-W/2)/(W*0.6), (gy-H/2)/(H*0.7))**2.6, 0.3, 1); img *= vig[..., None]
out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
out.save(OUT+'EPTC2026_holo_hands_AI_package_3840x2160.png', optimize=True)
out.resize((1920, 1080), Image.LANCZOS).save(OUT+'preview.png'); print('ok')
