"""Procedural epic-trailer score for the EPTC 2026 opening countdown.

120 BPM, D minor -> D major ending. Bar = 2 s.
  0-6   intro / "ARE YOU READY?" (text slam at 1.0 s)
  6-16  countdown 5,4,3,2,1 (one bar each, big hit on each downbeat)
  16    logo reveal: massive hit
  24    final D-major chord, rings out to 28 s
"""
import sys
import numpy as np
from scipy import signal

SR = 44100
DUR = 14.0
N = int((DUR + 3.0) * SR)
rng = np.random.default_rng(2026)

bus = {k: np.zeros((2, N)) for k in ("orch", "perc", "fx")}


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pan_gain(p):  # p in [-1, 1]
    a = (p + 1) * np.pi / 4
    return np.cos(a), np.sin(a)


def add(busname, x, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 < 0:
        x = x[-i0:]
        i0 = 0
    n = min(len(x), N - i0)
    if n <= 0:
        return
    gl, gr = pan_gain(pan)
    bus[busname][0, i0:i0 + n] += gain * gl * x[:n]
    bus[busname][1, i0:i0 + n] += gain * gr * x[:n]


def env_adsr(n, a, d, s, r_start, r):
    """a,d,r in seconds; r_start = time (s) release begins."""
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((t - r_start) / max(r, 1e-4), 0, None)
    e = e * np.where(t > r_start, np.exp(-4.5 * rel), 1.0)
    return e


def additive(f, n, gains_fn, vib=0.0, vib_rate=5.2, detune=0.0, fmax=14000.0):
    """Band-limited additive oscillator. gains_fn(k, fk) -> scalar or array(n)."""
    t = np.arange(n) / SR
    fi = f * 2 ** (detune / 1200) * (1 + vib * np.sin(2 * np.pi * vib_rate * t + rng.uniform(0, 6.28)))
    ph = 2 * np.pi * np.cumsum(fi) / SR + rng.uniform(0, 6.28)
    z = np.exp(1j * ph)
    zk = z.copy()
    out = np.zeros(n)
    K = int(fmax / f)
    for k in range(1, K + 1):
        g = gains_fn(k, k * f)
        if np.isscalar(g) and g < 1e-4:
            zk *= z
            continue
        out += g * zk.imag
        zk *= z
    return out


# ---------------------------------------------------------------- instruments
def brass(m, dur, amp=1.0, fc0=500, fc1=2200, swell=0.35, rel=0.6, voices=3, det=7, sat=1.6):
    f = mf(m)
    n = int((dur + rel + 0.1) * SR)
    t = np.arange(n) / SR
    # brightness swell then settle, with release darkening
    br = fc0 + (fc1 - fc0) * (1 - np.exp(-t / swell)) * np.exp(-np.clip(t - swell * 2, 0, None) / 2.5)
    br = np.maximum(br, fc0) * np.where(t > dur, np.exp(-(t - dur) / 0.4), 1) + 150
    fmax = min(12000.0, 4.0 * fc1)
    out = np.zeros(n)
    for v in range(voices):
        d = (v - (voices - 1) / 2) * det
        out += additive(f, n, lambda k, fk: (1.0 / k) / (1 + (fk / br) ** 2.5), vib=0.0025, detune=d, fmax=fmax)
    out /= voices
    out = np.tanh(sat * out) / np.tanh(sat)
    e = env_adsr(n, min(0.12, swell * 0.5), 0.6, 0.75, dur, rel)
    return amp * out * e


def braam(chord, dur=2.2, amp=1.0):
    out = None
    for m in chord:
        x = brass(m, dur, 1.0, fc0=350, fc1=3200, swell=0.08, rel=0.9, voices=4, det=14, sat=3.0)
        out = x if out is None else _sum(out, x)
    out = np.tanh(1.5 * out / len(chord) * 2.2)
    return amp * out


def _sum(a, b):
    n = max(len(a), len(b))
    o = np.zeros(n)
    o[:len(a)] += a
    o[:len(b)] += b
    return o


def string_note(m, dur, amp=1.0, voices=3, bright=5500):
    f = mf(m)
    n = int((dur + 0.25) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for v in range(voices):
        d = (v - (voices - 1) / 2) * 9
        out += additive(f, n, lambda k, fk: (1.0 / k) / (1 + (fk / bright) ** 2), vib=0.002, vib_rate=6,
                        detune=d, fmax=13000)
    e = np.minimum(t / 0.006, 1) * np.exp(-t / (dur * 0.9 + 0.03))
    return amp * out / voices * e


FORM = [(750, 110, 1.0), (1180, 120, 0.55), (2600, 170, 0.22), (3300, 250, 0.08)]  # "ah"


def choir_note(m, dur, amp=1.0, voices=6, attack=0.5, rel=1.2):
    f = mf(m)
    n = int((dur + rel + 0.1) * SR)

    def g(k, fk):
        fg = sum(a / (1 + ((fk - fc) / bw) ** 2) for fc, bw, a in FORM)
        return (0.25 / np.sqrt(k)) + fg / np.sqrt(k)

    out = np.zeros(n)
    for v in range(voices):
        out += additive(f, n, g, vib=0.004, vib_rate=rng.uniform(4.6, 5.8), detune=rng.uniform(-14, 14),
                        fmax=6000)
    out /= voices
    # breath
    br = rng.standard_normal(n)
    br = signal.sosfilt(signal.butter(2, [600, 3000], "bandpass", fs=SR, output="sos"), br) * 0.04
    e = env_adsr(n, attack, 1.0, 0.9, dur, rel)
    return amp * (out + br) * e


def sub(m, dur, amp=1.0, rel=0.8):
    f = mf(m)
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return amp * x * env_adsr(n, 0.05, 1, 1, dur, rel)


def lp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "lowpass", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def taiko(amp=1.0, f0=58, decay=0.55):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 1.4 * np.exp(-t / 0.018))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / decay) + 0.35 * np.sin(1.58 * ph) * np.exp(-t / (decay * 0.5))
    skin = bp(rng.standard_normal(n), 150, 900) * np.exp(-t / 0.045) * 1.6
    x = np.tanh(1.8 * (body + skin))
    return amp * x


def timpani(m, amp=1.0, decay=1.4):
    f0 = mf(m)
    n = int(3 * SR)
    t = np.arange(n) / SR
    bend = 1 + 0.04 * np.exp(-t / 0.08)
    x = np.zeros(n)
    for r, a, dd in [(1, 1.0, 1.0), (1.5, 0.5, 0.7), (1.98, 0.35, 0.5), (2.44, 0.2, 0.35), (2.9, 0.12, 0.3)]:
        x += a * np.sin(2 * np.pi * np.cumsum(f0 * r * bend) / SR) * np.exp(-t / (decay * dd))
    x += lp(rng.standard_normal(n), 1200) * np.exp(-t / 0.03) * 0.8
    return amp * np.tanh(1.3 * x)


def boom(amp=1.0, decay=2.2, f_hi=140, f_lo=32):
    n = int((decay * 3) * SR)
    t = np.arange(n) / SR
    f = f_lo + (f_hi - f_lo) * np.exp(-t / 0.12)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)
    crack = lp(rng.standard_normal(n), 3500) * np.exp(-t / 0.05) * 0.9
    rumble = lp(rng.standard_normal(n), 180) * np.exp(-t / (decay * 0.7)) * 0.6
    return amp * np.tanh(1.6 * (x + crack + rumble))


def crash(amp=1.0, decay=2.6, dur=4.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 2500, 3)
    x += 0.5 * bp(rng.standard_normal(n), 5000, 9000)
    return amp * x * np.exp(-t / decay) * np.minimum(t / 0.002, 1)


def reverse_cymbal(length, amp=1.0):
    x = crash(1.0, decay=length * 0.45, dur=length)[::-1]
    return amp * x


def snare(amp=1.0):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
    nz = bp(rng.standard_normal(n), 1200, 8000) * np.exp(-t / 0.09)
    return amp * (0.6 * tone + nz)


def snare_roll(t0, t1, amp0=0.1, amp1=0.8):
    t = t0
    while t < t1:
        u = (t - t0) / (t1 - t0)
        add("perc", snare(amp0 + (amp1 - amp0) * u ** 1.5), t, pan=rng.uniform(-0.2, 0.2))
        t += 0.125 * (1 - 0.65 * u)  # 16ths accelerating toward 32nds+


def riser(length, amp=1.0, f0=250, f1=7000):
    n = int(length * SR)
    x = rng.standard_normal(n)
    f, tt, Z = signal.stft(x, SR, nperseg=2048)
    u = np.clip(tt / length, 0, 1)
    center = f0 * (f1 / f0) ** (u ** 1.3)
    W = np.exp(-0.5 * (np.log2(np.maximum(f[:, None], 1) / center[None, :]) / 0.55) ** 2)
    _, y = signal.istft(Z * W, SR, nperseg=2048)
    y = y[:n]
    y = y / (np.abs(y).max() + 1e-9)
    t = np.arange(n) / SR
    # pitched shepard-ish sweep underneath
    fs = 110 * 2 ** (3 * (t / length) ** 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(fs) / SR) * 0.35
    e = (t / length) ** 2.2
    return amp * (y + tone) * e


def whoosh(length=0.6, amp=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    f, tt, Z = signal.stft(x, SR, nperseg=1024)
    u = np.clip(tt / length, 0, 1)
    center = 400 * (6000 / 400) ** np.sin(np.pi * u)
    W = np.exp(-0.5 * (np.log2(np.maximum(f[:, None], 1) / center[None, :]) / 0.7) ** 2)
    _, y = signal.istft(Z * W, SR, nperseg=1024)
    y = y[:n] / (np.abs(y[:n]).max() + 1e-9)
    return amp * y * np.sin(np.pi * t / length) ** 2


def tick(amp=1.0):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 2350 * t) + 0.5 * np.sin(2 * np.pi * 4700 * t)) * np.exp(-t / 0.012)
    return amp * x


# ---------------------------------------------------------------- harmony
CH = {  # low brass, horns (mid), strings root, third (semitones), sub root
    "Dm": ([38, 45, 50, 53, 57], [62, 65, 69], 50, 3, 26),
    "Bb": ([34, 41, 46, 50, 53], [58, 62, 65], 46, 4, 22),
    "F": ([41, 48, 53, 57, 60], [65, 69, 72], 53, 4, 29),
    "C": ([36, 43, 48, 52, 55], [60, 64, 67], 48, 4, 24),
    "A": ([33, 40, 45, 49, 52], [61, 64, 69], 45, 4, 21),
    "D": ([38, 45, 50, 54, 57], [62, 66, 69, 74], 50, 4, 26),
    "Gm": ([31, 38, 43, 46, 50], [62, 67, 70], 43, 3, 19),
}

BEAT = 0.5
SIX = 0.125
ACCENT = {0, 3, 6, 8, 11, 14}


def ostinato(chord, t0, n16, amp, octave=0, pan=0.0):
    _, _, root, third, _ = CH[chord]
    pat = [0, 0, 7, 0, 12, 0, 7, 0, third + 12, 0, 7, 0, 12, 7, third, 7]
    for i in range(n16):
        m = root + octave + pat[i % 16]
        a = amp * (1.0 if (i % 16) in ACCENT else 0.55)
        x = string_note(m, 0.11, 1.7 * a, voices=3, bright=4500 + 2500 * ((i % 16) in ACCENT))
        add("orch", x, t0 + i * SIX, pan=pan + rng.uniform(-0.15, 0.15))


def brass_chord(chord, t0, dur, amp, low=True, mid=True, swell=0.3, fc1=2200):
    lowv, midv, _, _, s = CH[chord]
    if low:
        for j, m in enumerate(lowv):
            add("orch", brass(m, dur, amp * (0.3 if j < 2 else 0.55), fc1=fc1 * 1.4, swell=swell), t0, pan=-0.35 + 0.17 * j)
        add("orch", sub(s + 12, dur, amp * 0.25), t0)
    if mid:
        for j, m in enumerate(midv):
            add("orch", brass(m, dur, amp * 0.5, fc0=900, fc1=fc1 * 1.7, swell=swell, voices=3), t0,
                pan=0.4 - 0.25 * j)


def choir_chord(chord, t0, dur, amp, attack=0.4):
    lowv, midv, _, _, _ = CH[chord]
    notes = [lowv[2] + 12, lowv[3] + 12] + midv
    for j, m in enumerate(notes):
        add("orch", choir_note(m, dur, amp * 0.45, attack=attack), t0, pan=-0.6 + 1.2 * j / max(1, len(notes) - 1))


def big_hit(t, chord, amp=1.0, braam_amp=0.9, crash_amp=0.35):
    add("perc", boom(amp * 0.9), t)
    add("perc", taiko(amp * 0.9, f0=52, decay=0.7), t, pan=-0.2)
    add("perc", taiko(amp * 0.8, f0=61, decay=0.6), t + 0.012, pan=0.25)
    add("perc", timpani(CH[chord][4] + 12, amp * 0.7), t)
    lowv = CH[chord][0]
    add("orch", braam([lowv[0], lowv[1], lowv[2]], 1.6, braam_amp * 0.6), t)
    if crash_amp:
        add("fx", crash(crash_amp), t, pan=0.3)
        add("fx", crash(crash_amp * 0.8), t + 0.005, pan=-0.3)



# ================= LANDING CUE (14 s) =================
# 0-4 space | 4 entry hit | 4-8 descent through atmosphere | 8 MBS reveal | 11 touchdown | 11-12.6 smoke -> white | ring out
# space: low drone + ethereal choir, soft pulsing strings
add("orch", sub(26, 4.2, 0.35, rel=1.0), 0.0)
brass_chord("Dm", 0.2, 3.6, 0.32, mid=False, swell=1.8, fc1=800)
choir_chord("Dm", 0.0, 3.8, 0.75, attack=1.6)
ostinato("Dm", 1.0, 8, 0.16)
ostinato("Dm", 2.0, 16, 0.26)
add("fx", riser(2.2, 0.25), 1.8)
add("fx", reverse_cymbal(1.4, 0.35), 2.6)
snare_roll(3.25, 3.95, 0.05, 0.35)
# entry hit (4.0): fire of re-entry
big_hit(4.0, "Bb", 0.85, braam_amp=0.75, crash_amp=0.3)
for j, (ch, t) in enumerate([("Bb", 4.0), ("C", 6.0)]):
    brass_chord(ch, t, 1.9, 0.62 + 0.06 * j, swell=0.3, fc1=2100)
    ostinato(ch, t, 16, 0.42 + 0.04 * j)
    if j:
        ostinato(ch, t, 16, 0.22, octave=12, pan=0.25)
        choir_chord(ch, t, 1.9, 0.75, attack=0.4)
    for b, a in [(1.5, 0.5), (2, 0.7), (3, 0.6), (3.5, 0.5), (3.75, 0.55)]:
        add("perc", taiko(a * 0.9, f0=60), t + b * BEAT, pan=rng.uniform(-0.3, 0.3))
    add("fx", whoosh(0.8, 0.25), t + 1.4)
add("perc", taiko(0.8, f0=55), 6.0)
snare_roll(7.2, 7.95, 0.1, 0.6)
add("fx", reverse_cymbal(1.3, 0.45), 6.7)
# MBS reveal (8.0): majestic, D major-ish heroic lift  F -> G -> A
big_hit(8.0, "F", 0.95, braam_amp=0.7, crash_amp=0.4)
for j, (ch, t, d) in enumerate([("F", 8.0, 1.0), ("Gm", 9.0, 1.0), ("A", 10.0, 0.95)]):
    brass_chord(ch, t, d, 0.75 + 0.05 * j, swell=0.25, fc1=2400)
    choir_chord(ch, t, d, 0.95, attack=0.15)
    ostinato(ch, t, 8, 0.4)
    ostinato(ch, t, 8, 0.22, octave=12, pan=0.25)
    add("perc", taiko(0.75, f0=56), t, pan=-0.1)
    add("perc", taiko(0.5, f0=63), t + 0.75, pan=0.2)
snare_roll(10.3, 10.93, 0.15, 0.85)
add("fx", riser(1.8, 0.45), 9.2)
add("fx", reverse_cymbal(1.6, 0.55), 9.4)
# touchdown (11.0): biggest hit, then D major swell into white
big_hit(11.0, "D", 1.15, braam_amp=0.9, crash_amp=0.6)
add("perc", boom(0.9, decay=3.0, f_hi=110, f_lo=28), 11.0)
brass_chord("D", 11.0, 2.0, 0.85, swell=0.3, fc1=2600)
choir_chord("D", 11.0, 2.4, 1.15, attack=0.25)
add("orch", sub(26, 2.4, 0.6, rel=1.0), 11.0)
# smoke whoosh + bright swell into the white frame (~12.6)
add("fx", whoosh(1.6, 0.45), 11.1)
add("fx", riser(1.6, 0.35, f0=800, f1=9000), 11.0)
for m in (74, 78, 81, 86):  # high shimmering D major (strings/choir) into white
    add("orch", choir_note(m, 1.4, 0.22, attack=0.9, rel=1.0), 11.3, pan=rng.uniform(-0.5, 0.5))
add("fx", crash(0.28, decay=1.8), 12.6)
add("perc", timpani(38, 0.6), 12.6)
# ---------------------------------------------------------------- mix
def make_ir(rt60, length, lp_hz, pre=0.02):
    n = int(length * SR)
    t = np.arange(n) / SR
    ir = np.zeros((2, n))
    for c in range(2):
        nz = rng.standard_normal(n)
        bright = nz * np.exp(-6.91 * t / (rt60 * 0.45))
        dark = lp(nz, lp_hz) * np.exp(-6.91 * t / rt60)
        ir[c] = bright * 0.5 + dark * 1.6
    ir[:, :int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    return ir


def reverb(x, ir, wet):
    out = np.zeros_like(x)
    for c in range(2):
        y = signal.fftconvolve(x[c], ir[c])[:x.shape[1]]
        out[c] = y
    return x * (1 - wet * 0.3) + wet * out


hall = make_ir(3.2, 4.0, 2800)
orch = reverb(hp(bus["orch"], 28), hall, 0.55)
perc = reverb(hp(bus["perc"], 25), hall, 0.3)
fx = reverb(hp(bus["fx"], 150), hall, 0.4)

# pre-hit "breath": duck everything just before each impact so hits land harder
tt = np.arange(orch.shape[1]) / SR
duckg = np.ones_like(tt)
for h, depth, pre in [(4.0, 0.45, 0.10), (8.0, 0.45, 0.10), (11.0, 0.12, 0.2)]:
    m = (tt > h - pre) & (tt < h)
    u = (tt[m] - (h - pre)) / pre
    duckg[m] = np.minimum(duckg[m], 1 - (1 - depth) * np.clip(u * 4, 0, 1))
duckg = lp(duckg, 60, order=1)
mix = (1.0 * orch + 0.6 * perc + 0.7 * fx) * duckg
mix = hp(mix, 30)

# bus compressor (feed-forward RMS)
lvl = np.sqrt(lp(np.mean(mix ** 2, axis=0), 4, order=1).clip(1e-12))
ref = np.percentile(lvl, 70)
thr = ref * 1.0
gr = np.where(lvl > thr, (lvl / thr) ** (1 / 2.0 - 1), 1.0)
gr = lp(gr, 3, order=1)
mix = mix * gr
mix = mix / np.abs(mix).max() * 1.15
mix = np.tanh(mix) * 0.95

# fade tail
n_end = int(DUR * SR)
fade = int(0.9 * SR)
mix = mix[:, :n_end]
mix[:, -fade:] *= np.linspace(1, 0, fade) ** 1.5

from scipy.io import wavfile

out = sys.argv[1] if len(sys.argv) > 1 else "music_raw.wav"
wavfile.write(out, SR, (mix.T * 32767 * 0.98).astype(np.int16))
print("wrote", out, mix.shape, "peak", np.abs(mix).max())
