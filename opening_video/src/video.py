"""EPTC 2026 opening countdown — procedural renderer.

python video.py frames  t1 t2 ...   -> writes test PNGs
python video.py render  out.mp4     -> renders full silent video (rawvideo -> x264)
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
LOGO = os.path.join(HERE, "..", "..", "deck_src", "assets", "logo_trans.png")

W, H = 1024, 576
FPS = 30
DUR = 28.0
NF = int(DUR * FPS)
FOCAL = 820.0
CX, CY = W / 2, H / 2

BEATS = [6.0, 8.0, 10.0, 12.0, 14.0]  # countdown 5..1
LOGO_T = 16.0
FINAL_T = 24.0
TEXT_T = 1.0


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = min(max(x, 0.0), 1.0)
    return x ** 3


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


# ===================================================================== texture
TS = 2048
PPU = 128.0  # texels per world unit
NL = 6


def build_texture(seed=11):
    rng = np.random.default_rng(seed)
    base = np.zeros((TS, TS, 3), np.float32)
    base[:] = (0.016, 0.022, 0.040)
    low = rng.random((32, 32)).astype(np.float32)
    low = ndimage.zoom(low, TS / 32, order=1, mode="grid-wrap")
    base *= (0.75 + 0.5 * low)[..., None]
    # fine substrate grid
    g = np.zeros(TS, np.float32)
    g[::64] = 1
    g[1::64] = 0.5
    base += (np.maximum(g[:, None], g[None, :]) * 0.010)[..., None] * np.array([0.6, 0.9, 1.6], np.float32)

    mask = np.zeros((TS, TS), np.float32)
    phase = np.full((TS, TS), -1e9, np.float32)

    def disc(r):
        rr = int(math.ceil(r))
        yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
        m = (xx ** 2 + yy ** 2) <= r * r
        return np.stack([yy[m], xx[m]], 1)

    def fill_rect(x0, y0, w, h, col, add=False):
        rows = np.arange(int(y0), int(y0 + h)) % TS
        cols = np.arange(int(x0), int(x0 + w)) % TS
        if add:
            base[np.ix_(rows, cols)] += np.array(col, np.float32)
        else:
            base[np.ix_(rows, cols)] = np.array(col, np.float32)

    def stamp(cy, cx, r, col, glow=0.0):
        o = disc(r)
        yy = (o[:, 0] + int(cy)) % TS
        xx = (o[:, 1] + int(cx)) % TS
        base[yy, xx] = col

    COPPER = np.array([0.085, 0.042, 0.014], np.float32)
    PAD = np.array([0.30, 0.13, 0.035], np.float32)

    # chip footprints with pin rows / BGA fields
    for _ in range(26):
        w, h = rng.integers(90, 320, 2)
        x0, y0 = rng.integers(0, TS, 2)
        fill_rect(x0, y0, w, h, (0.030, 0.034, 0.048))
        fill_rect(x0 + 6, y0 + 6, w - 12, h - 12, (0.022, 0.025, 0.036))
        if rng.random() < 0.5:  # BGA field
            for yy in range(int(y0) + 14, int(y0 + h) - 10, 14):
                for xx in range(int(x0) + 14, int(x0 + w) - 10, 14):
                    stamp(yy, xx, 3.2, COPPER * 2.2)
        else:  # QFP pins
            for xx in range(int(x0) + 10, int(x0 + w) - 10, 9):
                fill_rect(xx, y0 - 12, 4, 12, PAD * 0.7)
                fill_rect(xx, y0 + h, 4, 12, PAD * 0.7)
            for yy in range(int(y0) + 10, int(y0 + h) - 10, 9):
                fill_rect(x0 - 12, yy, 12, 4, PAD * 0.7)
                fill_rect(x0 + w, yy, 12, 4, PAD * 0.7)

    # routed traces (with buses of parallel lines)
    dirs8 = np.array([(math.cos(a), math.sin(a)) for a in np.arange(8) * math.pi / 4])

    def polyline():
        p = rng.uniform(0, TS, 2)
        d = int(rng.choice([0, 2, 4, 6]))
        pts = [p.copy()]
        for _ in range(rng.integers(3, 8)):
            L = rng.uniform(40, 320)
            p = p + dirs8[d] * L
            pts.append(p.copy())
            d = (d + int(rng.choice([-1, 1, -2, 2, -1, 1]))) % 8
        return np.array(pts)

    def offset_poly(pts, off):
        segs = np.diff(pts, axis=0)
        segs /= np.linalg.norm(segs, axis=1, keepdims=True)
        nrm = np.stack([-segs[:, 1], segs[:, 0]], 1)
        out = [pts[0] + nrm[0] * off]
        for i in range(1, len(pts) - 1):
            m = nrm[i - 1] + nrm[i]
            m /= np.linalg.norm(m) + 1e-9
            k = off / max(np.dot(m, nrm[i - 1]), 0.3)
            out.append(pts[i] + m * k)
        out.append(pts[-1] + nrm[-1] * off)
        return np.array(out)

    def draw_trace(pts, width, amp, sign, offset):
        o = disc(width / 2)
        dist0 = 0.0
        allp, alld = [], []
        for a, b in zip(pts[:-1], pts[1:]):
            L = np.linalg.norm(b - a)
            n = max(int(L / 0.7), 2)
            u = np.linspace(0, 1, n, endpoint=False)
            allp.append(a[None] + (b - a)[None] * u[:, None])
            alld.append(dist0 + u * L)
            dist0 += L
        P = np.concatenate(allp)
        D = np.concatenate(alld)
        yy = (P[:, 1].astype(int)[:, None] + o[None, :, 0]) % TS
        xx = (P[:, 0].astype(int)[:, None] + o[None, :, 1]) % TS
        DD = np.broadcast_to(D[:, None], yy.shape)
        base[yy, xx] = COPPER
        mask[yy, xx] = amp
        phase[yy, xx] = sign * DD + offset
        # vias / pads at both ends
        for q in (pts[0], pts[-1]):
            stamp(q[1], q[0], width / 2 + 4.5, PAD)
            stamp(q[1], q[0], width / 2 + 1.5, np.array([0.02, 0.02, 0.03], np.float32))

    for _ in range(170):
        pts = polyline()
        nb = int(rng.choice([1, 1, 2, 3, 4, 6, 8]))
        width = float(rng.choice([2.5, 3, 3.5, 4.5]))
        spacing = width + rng.uniform(4, 8)
        for j in range(nb):
            off = (j - (nb - 1) / 2) * spacing
            pp = offset_poly(pts, off) if nb > 1 else pts
            amp = float(rng.choice([0.0, 0.35, 0.6, 1.0, 1.0]))
            draw_trace(pp, width, amp, float(rng.choice([-1, 1])), float(rng.uniform(0, 5000)))

    # mip chain
    bases, masks, phases = [base], [mask], [phase]
    for _ in range(1, NL):
        b = bases[-1]
        h2 = b.shape[0] // 2
        bases.append(b.reshape(h2, 2, h2, 2, 3).mean((1, 3)))
        m = masks[-1]
        masks.append(m.reshape(h2, 2, h2, 2).mean((1, 3)))
        p = phases[-1]
        phases.append(p.reshape(h2, 2, h2, 2).max((1, 3)))
    return bases, masks, phases


# ===================================================================== chips (3D boxes)
def chip_top_textures(seed=3):
    rng = np.random.default_rng(seed)
    out = []
    S = 256
    for v in range(5):
        im = Image.new("RGB", (S, S), (20, 22, 29))
        d = ImageDraw.Draw(im)
        inset = int(rng.integers(30, 70))
        d.rectangle([inset, inset, S - inset, S - inset], fill=(11, 12, 17))
        for k in range(inset + 10, S - inset, 14):
            d.line([(k, inset + 4), (k, S - inset - 4)], fill=(24, 26, 34))
            d.line([(inset + 4, k), (S - inset - 4, k)], fill=(24, 26, 34))
        glow = (255, 120, 28) if v % 2 == 0 else (255, 160, 60)
        d.rectangle([inset - 6, inset - 6, S - inset + 6, S - inset + 6], outline=glow, width=3)
        d.rectangle([3, 3, S - 4, S - 4], outline=(60, 40, 28), width=4)
        d.ellipse([12, 12, 26, 26], fill=(90, 60, 40))
        if v >= 3:  # heat-spreader logo marks
            for r in range(4):
                d.rectangle([inset + 16, inset + 16 + r * 14, inset + 16 + rng.integers(40, 110),
                             inset + 22 + r * 14], fill=(46, 48, 58))
        out.append(im)
    return out


def build_chips(seed=5):
    rng = np.random.default_rng(seed)
    chips = []
    cell = 2.7
    for gz in range(-2, 46):
        for gx in range(-6, 7):
            if rng.random() > 0.42:
                continue
            w = rng.uniform(0.7, 2.1)
            dpt = rng.uniform(0.7, 2.1)
            if rng.random() < 0.12:
                w = dpt = rng.uniform(2.0, 2.5)
            x0 = gx * cell + rng.uniform(0, cell - w)
            z0 = gz * cell + rng.uniform(0, cell - dpt)
            h = rng.uniform(0.07, 0.42)
            chips.append((x0, z0, x0 + w, z0 + dpt, h, int(rng.integers(0, 5))))
    return chips


# ===================================================================== camera
def speed(t):
    v = 2.3
    for b in BEATS + [LOGO_T]:
        v += 4.5 * math.exp(-((t - b - 0.08) / 0.22) ** 2)
    v += 1.2 * smooth((t - 2) / 4)
    v -= 2.2 * smooth((t - LOGO_T) / 3.0)
    v += 2.5 * math.exp(-((t - FINAL_T - 0.08) / 0.25) ** 2)
    return v


_ts = np.arange(0, DUR + 1, 1 / 600)
_zs = np.concatenate([[0], np.cumsum([speed(x) / 600 for x in _ts[:-1]])])


def shake(t):
    s = 0.0
    for b, a in [(TEXT_T, 0.5)] + [(b, 0.7) for b in BEATS] + [(LOGO_T, 1.3), (FINAL_T, 0.9)]:
        if t >= b:
            s += a * math.exp(-(t - b) / 0.18)
    return s


def camera(t):
    z = float(np.interp(t, _ts, _zs)) - 3.0
    x = 0.9 * math.sin(t * 0.21) + 0.4 * math.sin(t * 0.53)
    y = 1.0 + 0.08 * math.sin(t * 0.7) + 0.55 * smooth((t - LOGO_T) / 6)
    yaw = math.radians(5 * math.sin(t * 0.19 + 0.4) + 2 * math.sin(t * 0.47))
    pitch = math.radians(-4.5 - 3.5 * smooth((t - LOGO_T) / 6))
    roll = math.radians(-2.5 * math.sin(t * 0.19 + 0.9))
    sk = shake(t)
    if sk > 1e-3:
        r = np.random.default_rng(int(t * 1000))
        yaw += math.radians(r.uniform(-1, 1) * 0.5 * sk)
        pitch += math.radians(r.uniform(-1, 1) * 0.5 * sk)
    F = np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
    R0 = np.array([math.cos(yaw), 0.0, -math.sin(yaw)])
    U0 = np.cross(F, R0)
    R = R0 * math.cos(roll) + U0 * math.sin(roll)
    U = U0 * math.cos(roll) - R0 * math.sin(roll)
    return np.array([x, y, z]), F, R, U


# ===================================================================== static assets
TEX = None
CHIPS = None
TOPS = None
PXg = PYg = None
ORBS = DUST = None
OV = {}


def init():
    global TEX, CHIPS, TOPS, PXg, PYg, ORBS, DUST
    TEX = build_texture()
    CHIPS = build_chips()
    TOPS = chip_top_textures()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    PXg = xx + 0.5 - CX
    PYg = CY - (yy + 0.5)
    rng = np.random.default_rng(21)
    n = 46
    ORBS = dict(
        x=rng.uniform(-9, 9, n), y=rng.uniform(0.15, 1.3, n), z=rng.uniform(0, 110, n),
        ph=rng.uniform(0, 6.28, n), I=rng.uniform(0.6, 1.6, n),
        col=np.array([(1.0, 0.55, 0.12) if r < 0.75 else (1.0, 0.78, 0.45) for r in rng.random(n)], np.float32))
    m = 420
    DUST = dict(x=rng.uniform(-7, 7, m), y=rng.uniform(0.05, 2.6, m), z=rng.uniform(0, 24, m),
                I=rng.uniform(0.15, 0.6, m))
    build_overlays()


def text_rgba(text, fnt, fill=(255, 255, 255), tracking=0, grad=None, pad=40):
    # measure
    widths = [fnt.getlength(c) for c in text]
    tw = int(sum(widths) + tracking * (len(text) - 1))
    asc, desc = fnt.getmetrics()
    th = asc + desc
    im = Image.new("L", (tw + 2 * pad, th + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for c, w in zip(text, widths):
        d.text((x, pad), c, font=fnt, fill=255)
        x += w + tracking
    a = np.array(im, np.float32) / 255
    rgb = np.zeros(a.shape + (3,), np.float32)
    if grad is not None:
        ys = np.linspace(0, 1, a.shape[0])
        ys = np.clip((ys - pad / a.shape[0]) / (th / a.shape[0]), 0, 1)[:, None]
        top, bot = np.array(grad[0]) / 255, np.array(grad[1]) / 255
        rgb[:] = (top[None, None] * (1 - ys[..., None]) + bot[None, None] * ys[..., None])
    else:
        rgb[:] = np.array(fill) / 255
    return np.dstack([rgb, a])


def glow_of(rgba, sigma, color, strength=1.0):
    a = ndimage.gaussian_filter(rgba[..., 3], sigma)
    return np.dstack([np.ones(a.shape + (3,), np.float32) * np.array(color, np.float32), a * strength])


def hstack_rgba(parts, baseline_shift=None):
    """parts: list of (rgba, dy). Concatenate horizontally, aligning by top + dy."""
    pad = 40
    hmax = max(p.shape[0] + abs(dy) for p, dy in parts)
    wsum = sum(p.shape[1] - 2 * pad for p, _ in parts) + 2 * pad
    out = np.zeros((hmax + 10, wsum, 4), np.float32)
    x = 0
    for p, dy in parts:
        h, w = p.shape[:2]
        y0 = 5 + max(0, dy)
        sub = out[y0:y0 + h, x:x + w]
        a = p[..., 3:4]
        sub[...] = sub * (1 - a) + p * a
        sub[..., 3:4] = np.maximum(sub[..., 3:4], a)
        x += w - 2 * pad
    return out


def build_overlays():
    ready = text_rgba("ARE YOU READY?", font("russo.woff", 66), tracking=3,
                      grad=((255, 178, 70), (236, 60, 22)))
    OV["ready"] = ready
    OV["ready_glow"] = glow_of(ready, 14, (1.0, 0.35, 0.05), 1.3)
    nf = font("orbitron900.woff", 118)
    OV["digits"] = {}
    for d in "12345":
        r = text_rgba(d, nf, fill=(255, 255, 255))
        OV["digits"][d] = (r, glow_of(r, 10, (1.0, 0.45, 0.08), 1.6))
    # logo
    lg = Image.open(LOGO).convert("RGBA")
    lw = 430
    lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    a = np.array(lg, np.float32) / 255
    pad = 40
    big = np.zeros((a.shape[0] + 2 * pad, a.shape[1] + 2 * pad, 4), np.float32)
    big[pad:-pad, pad:-pad] = a
    OV["logo"] = big
    OV["logo_glow"] = glow_of(big, 16, (1.0, 0.33, 0.05), 0.9)
    mont = font("mont500.woff", 20)
    OV["line1"] = text_rgba("28TH ELECTRONICS PACKAGING TECHNOLOGY CONFERENCE", mont, tracking=1.1)
    OV["date"] = sup_line([("1", 0), ("st", 1), (" to 4", 0), ("th", 1), (" December 2026", 0)],
                          font("mont500.woff", 21), font("mont500.woff", 13))
    f19 = font("mont500.woff", 20)
    OV["b1"] = text_rgba("IEEE EPS Flagship Conference in Asia", f19, tracking=0.6)
    OV["b2"] = text_rgba("Singapore", f19, tracking=0.6)
    for k in ("line1", "date", "b1", "b2"):
        OV[k + "_glow"] = glow_of(OV[k], 6, (1.0, 0.5, 0.15), 0.35)


def sup_line(parts, fb, fs, pad=40):
    asc, desc = fb.getmetrics()
    tw = sum((fs if sup else fb).getlength(tx) + (1 if sup else 0) for tx, sup in parts)
    im = Image.new("L", (int(tw) + 2 * pad, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    x = pad
    base = pad + asc
    for tx, sup in parts:
        f = fs if sup else fb
        d.text((x + (1 if sup else 0), base - (8 if sup else 0)), tx, font=f, fill=255, anchor="ls")
        x += f.getlength(tx) + (1 if sup else 0)
    a = np.array(im, np.float32) / 255
    return np.dstack([np.ones(a.shape + (3,), np.float32), a])


def _sup_line(parts):
    pad = 40
    # baseline align: big text top at y=pad; superscript raised so its top sits ~4px above big text cap
    H0 = max(p.shape[0] for p, _ in parts) + 20
    wsum = sum(p.shape[1] - 2 * pad for p, _ in parts) + 2 * pad
    out = np.zeros((H0, wsum, 4), np.float32)
    x = 0
    for p, dy in parts:
        h, w = p.shape[:2]
        y0 = 10 + (dy if dy < 0 else 0) + 10
        y0 = max(0, y0)
        sub = out[y0:y0 + h, x:x + w]
        a = p[..., 3:4]
        sub[..., :3] = sub[..., :3] * (1 - a) + p[..., :3] * a
        sub[..., 3:4] = np.maximum(sub[..., 3:4], a)
        x += w - 2 * pad
    return out


# ===================================================================== compositing helpers
def resize_rgba(rgba, s):
    if abs(s - 1) < 1e-3:
        return rgba
    h, w = rgba.shape[:2]
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    chans = [np.array(Image.fromarray(rgba[..., c]).resize((nw, nh), Image.BILINEAR)) for c in range(4)]
    return np.dstack(chans)


def place(dst, rgba, cx, cy, alpha=1.0, mode="over", gain=1.0):
    h, w = rgba.shape[:2]
    x0 = int(round(cx - w / 2))
    y0 = int(round(cy - h / 2))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return
    src = rgba[ya - y0:yb - y0, xa - x0:xb - x0]
    a = src[..., 3:4] * alpha
    if mode == "over":
        dst[ya:yb, xa:xb] = dst[ya:yb, xa:xb] * (1 - a) + src[..., :3] * gain * a
    else:
        dst[ya:yb, xa:xb] += src[..., :3] * a * gain


def glitch(rgba, amount, seed):
    if amount < 0.02:
        return rgba
    r = np.random.default_rng(seed)
    out = rgba.copy()
    h = rgba.shape[0]
    y = 0
    while y < h:
        sh = int(r.integers(3, 14))
        if r.random() < 0.5:
            dx = int(r.normal(0, 18 * amount))
            out[y:y + sh] = np.roll(rgba[y:y + sh], dx, axis=1)
        y += sh
    # chromatic split
    d = int(6 * amount) + 1
    out[..., 0] = np.roll(out[..., 0], d, axis=1)
    out[..., 2] = np.roll(out[..., 2], -d, axis=1)
    return out


# ===================================================================== HUD
def draw_hud(t, bar_t0, appear, scale=1.0):
    S2 = 2
    R = 104 * S2
    size = int(R * 2.7)
    c = size / 2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    al = lambda a: int(255 * a * appear)

    def arc(r, a0, a1, width, col):
        d.arc([c - r, c - r, c + r, c + r], a0, a1, fill=col, width=int(width))

    # translucent core
    d.ellipse([c - 0.9 * R, c - 0.9 * R, c + 0.9 * R, c + 0.9 * R], fill=(6, 6, 10, al(0.55)))
    # outer thin ring with rotating gaps
    rot = t * 22
    for k in range(4):
        arc(1.2 * R, rot + k * 90 + 8, rot + k * 90 + 82, 3, (255, 255, 255, al(0.55)))
    # tick ring
    rot2 = -t * 9
    for k in range(72):
        ang = math.radians(rot2 + k * 5)
        r0 = 1.05 * R
        r1 = 1.12 * R if k % 6 else 1.15 * R
        col = (255, 150, 60, al(0.85)) if k % 18 == 0 else (255, 255, 255, al(0.45))
        d.line([(c + r0 * math.cos(ang), c + r0 * math.sin(ang)), (c + r1 * math.cos(ang), c + r1 * math.sin(ang))],
               fill=col, width=3 if k % 6 == 0 else 2)
    # thick main arcs (white)
    rot3 = t * 48
    for a0, a1 in [(0, 105), (128, 196), (214, 334)]:
        arc(R, rot3 + a0, rot3 + a1, 0.075 * R, (255, 255, 255, al(0.95)))
    # counter-rotating orange segments
    rot4 = -t * 70
    for a0, a1 in [(10, 40), (190, 205), (250, 262)]:
        arc(0.935 * R, rot4 + a0, rot4 + a1, 0.03 * R, (255, 140, 40, al(0.95)))
    # countdown progress arc
    p = min(max((t - bar_t0) / 2.0, 0), 1)
    if p < 1:
        arc(0.84 * R, -90, -90 + 360 * (1 - p), 0.035 * R, (255, 120, 30, al(1.0)))
    # inner dotted ring
    for k in range(48):
        ang = math.radians(k * 7.5 + t * 15)
        x, y = c + 0.76 * R * math.cos(ang), c + 0.76 * R * math.sin(ang)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 255, al(0.35)))
    # wafer notch marker
    d.polygon([(c, c - 1.3 * R), (c - 9, c - 1.42 * R), (c + 9, c - 1.42 * R)], fill=(255, 140, 40, al(1)))
    im = im.reduce(S2)
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    a = np.array(im, np.float32) / 255
    return a


# ===================================================================== frame
def render_ground(t, cam, F, R, U):
    bases, masks, phases = TEX
    dx = F[0] * FOCAL + R[0] * PXg + U[0] * PYg
    dy = F[1] * FOCAL + R[1] * PXg + U[1] * PYg
    dz = F[2] * FOCAL + R[2] * PXg + U[2] * PYg
    dn = np.sqrt(dx * dx + dy * dy + dz * dz)
    elev = dy / dn
    ground = dy < -1e-6
    tt = np.where(ground, -cam[1] / np.where(ground, dy, -1), 0)
    X = cam[0] + tt * dx
    Z = cam[2] + tt * dz
    dist = tt * dn
    out = np.zeros((H, W, 3), np.float32)
    emis = np.zeros((H, W), np.float32)

    fp = dist * PPU / FOCAL / np.sqrt(np.maximum(-elev, 0.03))
    lvl = np.clip(np.floor(np.log2(np.maximum(fp, 1e-6)) + 0.35), 0, NL - 1).astype(np.int32)
    gidx = np.nonzero(ground)
    Lg = lvl[gidx]
    Xg, Zg = X[gidx], Z[gidx]
    col = np.zeros((len(Lg), 3), np.float32)
    em = np.zeros(len(Lg), np.float32)
    PER, VEL, TAIL = 900.0, 420.0, 140.0
    for L in range(NL):
        s = Lg == L
        if not s.any():
            continue
        size = TS >> L
        msk = size - 1
        uf = (Xg[s] * PPU / (1 << L) - 0.5).astype(np.float32)
        vf = (Zg[s] * PPU / (1 << L) - 0.5).astype(np.float32)
        u0f, v0f = np.floor(uf), np.floor(vf)
        fu, fv = (uf - u0f)[:, None], (vf - v0f)[:, None]
        u0 = u0f.astype(np.int64) & msk
        v0 = v0f.astype(np.int64) & msk
        u1, v1 = (u0 + 1) & msk, (v0 + 1) & msk
        B = bases[L]
        col[s] = (B[v0, u0] * (1 - fu) * (1 - fv) + B[v0, u1] * fu * (1 - fv) +
                  B[v1, u0] * (1 - fu) * fv + B[v1, u1] * fu * fv)
        M = masks[L]
        fu1, fv1 = fu[:, 0], fv[:, 0]
        m = (M[v0, u0] * (1 - fu1) * (1 - fv1) + M[v0, u1] * fu1 * (1 - fv1) +
             M[v1, u0] * (1 - fu1) * fv1 + M[v1, u1] * fu1 * fv1)
        P = phases[L]
        ph = np.maximum(np.maximum(P[v0, u0], P[v0, u1]), np.maximum(P[v1, u0], P[v1, u1]))
        dd = np.mod(ph - VEL * t, PER)
        e = np.exp(-(PER - dd) / TAIL) + np.exp(-dd / 4.0)
        em[s] = m * e
    out[gidx] = col
    emis[gidx] = em

    near = np.exp(-dist / 5.5)
    light = (0.55 + 1.5 * near)
    out *= light[..., None]
    pulse_gain = 1.0
    for b in BEATS + [LOGO_T, FINAL_T, TEXT_T]:
        if t >= b:
            pulse_gain += 2.0 * math.exp(-(t - b) / 0.35)
    ecol = np.array([1.7, 0.62, 0.12], np.float32)
    out += (emis * pulse_gain)[..., None] * ecol + (np.minimum(emis, 1.5) ** 4 * 0.35)[..., None]

    # fog & sky
    fog = np.exp(-dist / 15.0)
    horizon = np.array([0.22, 0.085, 0.025], np.float32)
    skyhi = np.array([0.006, 0.008, 0.02], np.float32)
    e = np.maximum(elev, 0)
    sky = skyhi + horizon * np.exp(-e / 0.035)[..., None] + np.array([0.05, 0.02, 0.01]) * np.exp(-e / 0.15)[..., None]
    fogcol = horizon * 0.8
    out = np.where(ground[..., None], out * fog[..., None] + fogcol * (1 - fog[..., None]), sky)
    return out.astype(np.float32)


def solve_persp(dst_pts, src_pts):
    A = []
    B = []
    for (x, y), (X, Y) in zip(dst_pts, src_pts):
        A.append([x, y, 1, 0, 0, 0, -X * x, -X * y])
        A.append([0, 0, 0, x, y, 1, -Y * x, -Y * y])
        B += [X, Y]
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def render_chips(t, cam, F, R, U):
    SS = 2
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = FOCAL * SS
    cx, cy = CX * SS, CY * SS
    vis = []
    for ch in CHIPS:
        x0, z0, x1, z1, h, k = ch
        mz = (z0 + z1) / 2 - cam[2]
        if mz < -3 or mz > 34:
            continue
        vis.append((mz, ch))
    vis.sort(key=lambda a: -a[0])
    fogc = np.array([0.22, 0.085, 0.025]) * 0.8 * 255
    for _, (x0, z0, x1, z1, h, k) in vis:
        P = np.array([[x0, 0, z0], [x1, 0, z0], [x1, 0, z1], [x0, 0, z1],
                      [x0, h, z0], [x1, h, z0], [x1, h, z1], [x0, h, z1]], float)
        rel = P - cam
        zc = rel @ F
        if zc.min() < 0.25:
            continue
        sx = cx + f * (rel @ R) / zc
        sy = cy - f * (rel @ U) / zc
        if sx.max() < 0 or sx.min() > W * SS or sy.max() < 0 or sy.min() > H * SS:
            continue
        dist = float(np.linalg.norm(rel.mean(0)))
        fk = math.exp(-dist / 15.0)

        def fogged(c):
            c = np.array(c, float)
            return tuple(int(v) for v in (c * fk + fogc * (1 - fk))) + (255,)

        pts = list(zip(sx, sy))
        # side faces
        if cam[2] < z0:
            d.polygon([pts[0], pts[1], pts[5], pts[4]], fill=fogged((13, 14, 20)))
        if cam[2] > z1:
            d.polygon([pts[3], pts[2], pts[6], pts[7]], fill=fogged((10, 11, 16)))
        if cam[0] < x0:
            d.polygon([pts[0], pts[3], pts[7], pts[4]], fill=fogged((8, 9, 13)))
        if cam[0] > x1:
            d.polygon([pts[1], pts[2], pts[6], pts[5]], fill=fogged((8, 9, 13)))
        # top face (textured)
        quad = [pts[7], pts[6], pts[5], pts[4]]  # far-left, far-right, near-right, near-left
        qx = [p[0] for p in quad]
        qy = [p[1] for p in quad]
        bx0, by0 = int(math.floor(min(qx))), int(math.floor(min(qy)))
        bx1, by1 = int(math.ceil(max(qx))), int(math.ceil(max(qy)))
        bw, bh = bx1 - bx0, by1 - by0
        if bw < 2 or bh < 2 or bw > W * SS * 2 or bh > H * SS * 2:
            continue
        tex = TOPS[k]
        S = tex.width
        try:
            coef = solve_persp([(x - bx0, y - by0) for x, y in quad], [(0, 0), (S, 0), (S, S), (0, S)])
        except np.linalg.LinAlgError:
            continue
        warped = tex.transform((bw, bh), Image.PERSPECTIVE, tuple(coef), Image.BILINEAR)
        if fk < 0.999:
            fogim = Image.new("RGB", (bw, bh), tuple(int(v) for v in fogc))
            warped = Image.blend(fogim, warped, fk)
        m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(m).polygon([(x - bx0, y - by0) for x, y in quad], fill=255)
        layer.paste(warped, (bx0, by0), m)
        # glowing rim on near top edge
        rim = fogged((255, 120, 35))
        d.line([pts[4], pts[5]], fill=rim, width=2)
    layer = layer.reduce(SS)
    a = np.array(layer, np.float32) / 255
    return a


def add_sprite(img, x, y, sigma, col, inten):
    r = int(sigma * 3.5) + 1
    x0, x1 = int(x) - r, int(x) + r + 1
    y0, y1 = int(y) - r, int(y) + r + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    yy, xx = np.mgrid[ya:yb, xa:xb]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sigma * sigma)).astype(np.float32)
    img[ya:yb, xa:xb] += g[..., None] * (np.array(col, np.float32) * inten)


def render_orbs(img, t, cam, F, R, U):
    o = ORBS
    camz = cam[2]
    # wrap orbs ahead of camera
    z = (o["z"] - camz) % 60.0 + camz - 2
    x = o["x"] + 0.4 * np.sin(t * 0.6 + o["ph"])
    y = o["y"] + 0.15 * np.sin(t * 1.1 + o["ph"] * 2)
    P = np.stack([x, y, z], 1)
    rel = P - cam
    zc = rel @ F
    for i in np.argsort(-zc):
        if zc[i] < 0.4:
            continue
        sx = CX + FOCAL * (rel[i] @ R) / zc[i]
        sy = CY - FOCAL * (rel[i] @ U) / zc[i]
        size = 0.09 * FOCAL / zc[i]
        fk = math.exp(-zc[i] / 22)
        flick = 0.75 + 0.25 * math.sin(t * 7 + o["ph"][i] * 5)
        I = o["I"][i] * fk * flick
        add_sprite(img, sx, sy, max(size * 0.35, 0.8), o["col"][i], I * 2.2)
        add_sprite(img, sx, sy, max(size * 1.6, 2.0), o["col"][i], I * 0.35)
    # dust
    dd = DUST
    z = (dd["z"] - camz) % 24.0 + camz + 0.3
    P = np.stack([dd["x"] + 0.2 * np.sin(t * 0.3 + dd["y"] * 5), dd["y"], z], 1)
    rel = P - cam
    zc = rel @ F
    ok = zc > 0.3
    sx = CX + FOCAL * (rel @ R) / np.where(ok, zc, 1)
    sy = CY - FOCAL * (rel @ U) / np.where(ok, zc, 1)
    ok &= (sx >= 1) & (sx < W - 1) & (sy >= 1) & (sy < H - 1)
    I = dd["I"] * np.exp(-zc / 12) * np.clip(zc / 1.5, 0, 1)
    xi, yi = sx[ok].astype(int), sy[ok].astype(int)
    col = np.array([1.0, 0.6, 0.25], np.float32)
    np.add.at(img, (yi, xi), (I[ok][:, None] * col).astype(np.float32))
    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        np.add.at(img, (yi + ddy, xi + ddx), (I[ok][:, None] * col * 0.35).astype(np.float32))


def bloom(img):
    br = np.maximum(img - 0.42, 0)
    small = br.reshape(H // 4, 4, W // 4, 4, 3).mean((1, 3))
    b1 = ndimage.gaussian_filter(small, (2, 2, 0))
    b2 = ndimage.gaussian_filter(small, (9, 9, 0))
    hot = np.maximum(small - 0.4, 0)
    st = ndimage.gaussian_filter(hot, (0.6, 40, 0)) * np.array([1.0, 0.55, 0.25])
    acc = 0.9 * b1 + 1.1 * b2 + 1.6 * st
    up = ndimage.zoom(acc, (4, 4, 1), order=1)
    return img + up.astype(np.float32)


VIG = None


def finish(img, t):
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((xx - CX) / (W / 2)) ** 2 + ((yy - CY) / (H / 2)) ** 2
        VIG = (1 - 0.32 * r2).clip(0.3, 1)[..., None]
    img = img * VIG
    k = 0.78
    img = np.where(img < k, img, k + (1 - k) * np.tanh((img - k) / (1 - k)))
    rng = np.random.default_rng(int(t * 1000) + 7)
    img = img + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    # global fade in / out
    fade = ramp(t, 0.0, 0.7) * (1 - ramp(t, 26.9, 27.95))
    img = img * fade
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


HUD_C = (CX, 272)


def render_frame(fi):
    t = fi / FPS
    cam, F, R, U = camera(t)
    img = render_ground(t, cam, F, R, U)
    ch = render_chips(t, cam, F, R, U)
    a = ch[..., 3:4]
    img = img * (1 - a) + ch[..., :3] * a * 1.15
    render_orbs(img, t, cam, F, R, U)
    img = bloom(img)

    sk = shake(t)
    jr = np.random.default_rng(fi)
    jx, jy = (jr.uniform(-1, 1) * 4 * sk, jr.uniform(-1, 1) * 4 * sk) if sk > 0.02 else (0, 0)

    # ---------------- ARE YOU READY?
    if TEXT_T <= t < 5.8:
        lt = t - TEXT_T
        s = 1.0 + 0.55 * (1 - ease_out(lt / 0.22)) + 0.035 * lt / 4.5
        alpha = ramp(t, TEXT_T, TEXT_T + 0.08) * (1 - ramp(t, 5.35, 5.7))
        gl = max(1 - lt / 0.35, 0) + ramp(t, 5.3, 5.6) * 0.9
        rr = glitch(resize_rgba(OV["ready"], s), gl, fi)
        gg = resize_rgba(OV["ready_glow"], s)
        place(img, gg, CX + jx, 150 + jy, alpha * (0.9 + 1.2 * max(1 - lt / 0.4, 0)), mode="add")
        place(img, rr, CX + jx, 150 + jy, alpha)

    # ---------------- converging light rings (transitions)
    for b in [BEATS[0]] + BEATS[1:] + [LOGO_T]:
        if b - 0.45 <= t < b:
            u = ease_in((t - (b - 0.45)) / 0.45)
            rmax = 700.0
            r = rmax * (1 - u) + 104 * u
            ring = ring_img(r, 3 + 6 * u, 0.45 + 1.2 * u)
            place(img, ring, HUD_C[0], HUD_C[1], 1.0, mode="add")
        if b <= t < b + 0.6:
            u = (t - b) / 0.6
            r = 104 + 560 * ease_out(u)
            ring = ring_img(r, 10 * (1 - u) + 2, 1.6 * (1 - u))
            place(img, ring, HUD_C[0], HUD_C[1], 1.0, mode="add")

    # ---------------- countdown HUD + digits
    if BEATS[0] - 0.05 <= t < LOGO_T + 0.45:
        bi = max(i for i, b in enumerate(BEATS) if t >= b - 0.05) if t >= BEATS[0] - 0.05 else 0
        b0 = BEATS[bi]
        appear = ramp(t, BEATS[0] - 0.05, BEATS[0] + 0.12)
        hs = 1.0 + 0.12 * math.exp(-max(t - b0, 0) / 0.12)
        if t >= LOGO_T - 0.05:
            u = (t - (LOGO_T - 0.05)) / 0.5
            hs = 1.0 + 1.8 * ease_out(u)
            appear *= max(1 - u, 0)
        if appear > 0.01:
            hud = draw_hud(t, b0, appear, hs)
            hg = glow_of(hud, 7, (1.0, 0.45, 0.1), 0.9)
            place(img, hg, HUD_C[0] + jx, HUD_C[1] + jy, 1.0, mode="add")
            place(img, hud, HUD_C[0] + jx, HUD_C[1] + jy, 1.0)
        if t < LOGO_T - 0.3:
            digit = "54321"[bi]
            lt = t - b0
            ds = 1.0 + 0.45 * (1 - ease_out(lt / 0.18))
            out_u = ramp(t, b0 + 1.62, b0 + 1.9)
            ds *= 1 - 0.25 * out_u
            alpha = ramp(t, b0 - 0.02, b0 + 0.06) * (1 - out_u)
            dr, dg = OV["digits"][digit]
            gl = max(1 - lt / 0.25, 0) + out_u
            place(img, resize_rgba(dg, ds), HUD_C[0] + jx, HUD_C[1] + jy, alpha * (1.0 + 1.5 * max(1 - lt / 0.3, 0)),
                  mode="add")
            place(img, glitch(resize_rgba(dr, ds), gl * 0.8, fi), HUD_C[0] + jx, HUD_C[1] + jy, alpha)

    # ---------------- logo section
    if t >= LOGO_T - 0.02:
        lt = t - LOGO_T
        # darken top/bottom bands for legibility
        k = ramp(t, LOGO_T, LOGO_T + 0.6)
        yy = np.arange(H, dtype=np.float32)
        band = 1 - k * (0.55 * np.exp(-((yy - 150) / 150) ** 2) + 0.5 * np.exp(-((yy - 500) / 90) ** 2))
        img *= band[:, None, None]
        s = 1.0 + 0.14 * (1 - ease_out(lt / 0.7)) + 0.03 * smooth(lt / 11)
        alpha = ramp(t, LOGO_T - 0.02, LOGO_T + 0.12)
        lg = OV["logo"]
        lgw = lg.copy()
        # glint sweeps
        for gt in (LOGO_T + 0.9, FINAL_T):
            if gt <= t < gt + 0.9:
                xs = np.arange(lg.shape[1], dtype=np.float32)
                ys = np.arange(lg.shape[0], dtype=np.float32)
                pos = -100 + (lg.shape[1] + 200) * smooth((t - gt) / 0.9)
                bandg = np.exp(-(((xs[None, :] - pos) + 0.45 * (ys[:, None] - lg.shape[0] / 2)) / 18) ** 2)
                lgw[..., :3] = lgw[..., :3] + bandg[..., None] * 0.85
        gglow = 0.55 + 2.2 * math.exp(-lt / 0.35)
        if t >= FINAL_T:
            gglow += 1.2 * math.exp(-(t - FINAL_T) / 0.4)
        place(img, resize_rgba(OV["logo_glow"], s), CX + jx, 128 + jy, alpha * gglow, mode="add")
        lgr = resize_rgba(lgw, s)
        if lt < 0.4:
            lgr = glitch(lgr, (0.4 - lt) * 1.5, fi)
        place(img, lgr, CX + jx, 128 + jy, alpha)

        # rules + conference title
        ru = ease_out((t - (LOGO_T + 0.9)) / 0.7)
        if ru > 0:
            l1 = OV["line1"]
            tw = l1.shape[1] - 80
            gap = 16
            ly = 240 + jy
            L = 70 * ru
            for sgn in (-1, 1):
                xa = CX + sgn * (tw / 2 + gap)
                xb = xa + sgn * L
                x0, x1 = int(min(xa, xb)), int(max(xa, xb))
                img[int(ly) - 1:int(ly) + 1, max(0, x0):min(W, x1)] = img[int(ly) - 1:int(ly) + 1,
                                                                          max(0, x0):min(W, x1)] * 0.1 + 0.95
        for key, y, t0 in (("line1", 240, LOGO_T + 1.05), ("date", 268, LOGO_T + 1.45),
                           ("b1", 470, LOGO_T + 2.2), ("b2", 498, LOGO_T + 2.45)):
            a = ramp(t, t0, t0 + 0.5)
            if a <= 0:
                continue
            dy = 10 * (1 - ease_out((t - t0) / 0.6))
            place(img, OV[key + "_glow"], CX + jx, y + dy + jy, a, mode="add")
            place(img, OV[key], CX + jx, y + dy + jy, a, gain=0.97)

    # ---------------- flashes
    fl = 0.0
    for b, a in [(0.0, 0.6), (TEXT_T, 0.35)] + [(b, 0.45) for b in BEATS] + [(LOGO_T, 1.3), (FINAL_T, 0.55)]:
        if t >= b:
            fl += a * math.exp(-(t - b) / 0.11)
    if fl > 0.003:
        yy, xx = np.ogrid[0:H, 0:W]
        rad = np.exp(-(((xx - HUD_C[0]) / 520.0) ** 2 + ((yy - HUD_C[1]) / 330.0) ** 2)).astype(np.float32)
        img += (fl * (0.35 + 0.9 * rad))[..., None] * np.array([1.0, 0.62, 0.32], np.float32)

    return finish(img, t)


_ring_cache = {}


def ring_img(r, width, inten):
    size = int(2 * r + 4 * width + 60)
    yy, xx = np.ogrid[0:size, 0:size]
    c = size / 2
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    core = np.exp(-((d - r) / max(width * 0.5, 0.8)) ** 2)
    halo = np.exp(-((d - r) / (width * 3 + 8)) ** 2) * 0.35
    a = ((core + halo) * inten).astype(np.float32)
    rgb = np.zeros((size, size, 3), np.float32)
    rgb[:] = (1.0, 0.55, 0.15)
    rgb = rgb + core[..., None] * 0.6
    return np.dstack([rgb, a])


# ===================================================================== main
def _worker(fi):
    return render_frame(fi).tobytes()


if __name__ == "__main__":
    init()
    if sys.argv[1] == "frames":
        os.makedirs(os.path.join(HERE, "test"), exist_ok=True)
        for ts in sys.argv[2:]:
            fi = int(round(float(ts) * FPS))
            Image.fromarray(render_frame(fi)).save(os.path.join(HERE, "test", f"f_{float(ts):05.2f}.png"))
            print("frame", ts)
    elif sys.argv[1] == "render":
        out = sys.argv[2]
        import multiprocessing as mp

        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
                               "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        with mp.get_context("fork").Pool(4) as pool:
            for i, buf in enumerate(pool.imap(_worker, range(NF), chunksize=2)):
                ff.stdin.write(buf)
                if i % 60 == 0:
                    print("frame", i, "/", NF, flush=True)
        ff.stdin.close()
        ff.wait()
        print("done", out)
