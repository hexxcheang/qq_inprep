import numpy as np, cv2
from PIL import Image
im = np.asarray(Image.open('v8/src.png').convert('RGB')).astype(np.float32)
H, W, _ = im.shape
box = np.zeros((H, W), bool); box[68:152, 58:668] = True
bgest = cv2.medianBlur(im.astype(np.uint8), 31).astype(np.float32)
diff = np.abs(im - bgest).max(2); sat = im.max(2) - im.min(2)
mask = box & ((diff > 4) | (sat > 14))
mask[86:130, 64:152] = True                                   # whole logo rectangle (incl. its faint backing)
mask = cv2.dilate(mask.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & box | (mask & box)
dirs = [(1, 1), (1, -1)]
YY, XX = np.mgrid[0:H, 0:W]
edge_x = np.maximum(268 - YY, 43 + YY).astype(np.float32)       # left boundary of the leftmost chevron
inside = XX >= edge_x + 1
known = ~mask & (inside | (XX > 400))                             # interior samples only for the fill                       # (dy, dx): vertical, both diagonals, horizontal
out = im.copy()
ys, xs = np.where(mask & (inside | (XX > 400)))
for y, x in zip(ys, xs):
    best = None; single = None
    for dy, dx in dirs:
        ends = []
        for s in (1, -1):
            k = 1
            while True:
                yy, xx = y + s*dy*k, x + s*dx*k
                if not (0 <= yy < H and 0 <= xx < W): break
                if known[yy, xx]: ends.append((k, im[yy, xx])); break
                if not (inside[yy, xx] or xx > 400): break        # left the chevron: this side has no sample
                k += 1
                if k > 160: break
        if len(ends) == 1:
            k1, c1 = ends[0]
            if single is None or k1 < single[0]: single = (k1, c1)
            continue
        if len(ends) < 2: continue
        (k1, c1), (k2, c2) = ends
        err = np.abs(c1 - c2).sum() + 0.02*(k1 + k2)            # prefer agreeing, short spans
        if best is None or err < best[0]:
            best = (err, (c1*k2 + c2*k1)/(k1 + k2))
    if best is not None: out[y, x] = best[1]
    elif single is not None: out[y, x] = single[1]
# outside the chevron: pure white, with an anti-aliased edge
cov = np.clip(XX - edge_x + 0.5, 0, 1)[..., None]                # 0 outside, 1 inside
band = mask & (np.abs(XX - edge_x) < 2.5) & (XX < 400)
ref = np.roll(out, -3, axis=1)                                    # interior value just to the right of the edge
out[band] = (255*(1-cov) + ref*cov)[band]
outside_fill = mask & ~(inside | (XX > 400)) & ~band
out[outside_fill] = 255
# very light smoothing inside the fill only (removes interpolation streaks), keeps straight edges
sm = cv2.GaussianBlur(out, (0, 0), 0.6)
m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
out = out*(1-m) + sm*m
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save('v8/cleaned.png')
Image.fromarray(out).crop((40, 40, 720, 180)).resize((1360, 280)).save('v8/top2.png')
print('ok', int(mask.sum()))
