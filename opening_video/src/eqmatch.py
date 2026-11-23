"""Match long-term spectrum of IN to REF (smoothed, clamped), linear-phase FIR."""
import sys, numpy as np
from scipy import signal
from scipy.io import wavfile
ref, inp, out = sys.argv[1:4]
sr, r = wavfile.read(ref); r = r.astype(float); r = r.mean(1) if r.ndim > 1 else r
sr2, x = wavfile.read(inp); x = x.astype(float) / 32768
f, Pr = signal.welch(r, sr, nperseg=8192)
_, Px = signal.welch(x.mean(1), sr2, nperseg=8192)
Pr /= Pr.sum(); Px /= Px.sum()
# 1/3-octave smoothing in log domain
def smooth(P):
    out = np.empty_like(P)
    for i, fi in enumerate(f):
        m = (f >= fi / 2 ** (1 / 6)) & (f <= fi * 2 ** (1 / 6))
        out[i] = P[m].mean() if m.any() else P[i]
    return out
g = 10 * np.log10(smooth(Pr) + 1e-15) - 10 * np.log10(smooth(Px) + 1e-15)
g = np.clip(g, -9, 9)
g[f < 30] = np.minimum(g[f < 30], 0)
g[f > 12000] = np.minimum(g[f > 12000], 0)  # ref is band-limited (AAC), don't chase that
gl = 10 ** (g / 20)
taps = signal.firwin2(4097, f / (sr2 / 2), gl / gl.max() * gl.max())
y = np.stack([signal.fftconvolve(x[:, c], taps)[2048:2048 + len(x)] for c in range(2)], 1)
y = y / np.abs(y).max() * 0.97
wavfile.write(out, sr2, (y * 32767).astype(np.int16))
for lo, hi in [(20,60),(60,120),(120,250),(250,500),(500,1000),(1000,2000),(2000,4000),(4000,8000),(8000,16000)]:
    m=(f>=lo)&(f<hi); print(f'{lo}-{hi}: {g[m].mean():+.1f} dB')
