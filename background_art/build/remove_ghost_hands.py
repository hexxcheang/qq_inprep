import numpy as np, cv2
from PIL import Image
from scipy import ndimage
src = np.asarray(Image.open('v7/src.jpg').convert('RGB')).astype(np.float32)
H, W, _ = src.shape; R, G, B = src[..., 0], src[..., 1], src[..., 2]; lum = src.mean(2)
core = ((R - G > 85) & (R - B > 70) & (G < 120)).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(core, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)))
ids = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 800]
core = np.isin(lab, ids).astype(np.uint8)
loose = ((R - G > 55) & (R - B > 35) & (R > 95)).astype(np.uint8)           # pinkish JPEG fringe
near = cv2.dilate(core, np.ones((15, 15), np.uint8))
stroke = cv2.dilate(((core | (loose & near)) > 0).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
hull = np.zeros((H, W), np.uint8)
for i in ids:
    ys, xs = np.where(lab == i); cv2.fillConvexPoly(hull, cv2.convexHull(np.stack([xs, ys], 1).astype(np.int32)), 1)
hull = hull > 0
interior = hull & ~stroke
outside = ~hull & ~stroke
# --- navy background from empty pixels outside the loops
known = outside & (lum < 64) & (B > R + 4)
def pushpull(img, m):
    if min(img.shape[:2]) <= 4:
        v = (img*m[..., None]).sum((0, 1))/max(m.sum(), 1); return np.broadcast_to(v, img.shape).copy()
    w = cv2.GaussianBlur(m, (5, 5), 1.2); v = cv2.GaussianBlur(img*m[..., None], (5, 5), 1.2)
    sh = (img.shape[1]//2, img.shape[0]//2)
    sw, sv = cv2.resize(w, sh, interpolation=cv2.INTER_AREA), cv2.resize(v, sh, interpolation=cv2.INTER_AREA)
    mm = (sw > 1e-3).astype(np.float32)
    coarse = pushpull(np.where(mm[..., None] > 0, sv/np.maximum(sw[..., None], 1e-6), 0), mm)
    up = cv2.resize(coarse, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.where(m[..., None] > 0, img, up)
bg = cv2.GaussianBlur(pushpull(src, known.astype(np.float32)), (0, 0), 10)
# --- keep real content inside the loops (crisp gold lines, blue rings/sparkles)
ss = lambda x, a, b: np.clip((x-a)/(b-a), 0, 1)
keep = np.maximum(ss(R-B, 58, 82)*ss(lum, 110, 145), ss(B-R, 15, 35)*ss(B, 95, 125))
keep = cv2.GaussianBlur(keep, (0, 0), 0.7)
out = src.copy()
a = interior.astype(np.float32)*(1-keep)
out = out*(1-a[..., None]) + bg*a[..., None]
# --- stroke pixels: mirror texture from the outside across the stroke edge (restores thumbs), navy elsewhere
dist, (iy, ix) = ndimage.distance_transform_edt(~outside, return_indices=True)
sy, sx = np.where(stroke)
ny, nx = iy[sy, sx], ix[sy, sx]
ry = np.clip(2*ny - sy, 0, H-1); rx = np.clip(2*nx - sx, 0, W-1)
mir = src[ry, rx]
mir_ok = outside[ry, rx]
mir = np.where(mir_ok[:, None], mir, bg[sy, sx])
# blend: stroke side touching the interior fades to the background
din = ndimage.distance_transform_edt(~interior)[sy, sx]; dout = dist[sy, sx]
t = np.clip(dout/(din+dout+1e-6), 0, 1)[:, None]         # 0 at outside edge, 1 at interior edge
k_in = keep[sy, sx][:, None]
fill = mir*(1-t) + (bg[sy, sx]*(1-k_in) + mir*k_in)*t
out[sy, sx] = fill
# soften seams & grain
seam = cv2.GaussianBlur(stroke.astype(np.float32), (0, 0), 2.0)
sm = cv2.GaussianBlur(out, (0, 0), 1.0)
out = out*(1-0.6*seam[..., None]) + sm*0.6*seam[..., None]
g = np.random.default_rng(2).normal(0, 2.2, out.shape)
out += g*np.maximum(a, stroke.astype(np.float32))[..., None]
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save('v7/cleaned.png')
Image.fromarray(out).crop((150, 170, 470, 600)).resize((640, 860)).save('v7/L2.png')
Image.fromarray(out).crop((880, 180, 1200, 580)).resize((640, 800)).save('v7/R2.png')
print('ok')
