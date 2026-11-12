import numpy as np, cv2
from PIL import Image
im = np.asarray(Image.open('v9/base.png').convert('RGB')).astype(np.float32)
H, W, _ = im.shape
X0, X1, Y0, Y1 = 62, 712, 190, 530                       # text block region
DY = -133                                                # shift up
QR_X, QR_Y, QR_S = 74, 408, 174       # white card (x, y, size)
box = np.zeros((H, W), bool); box[Y0:Y1, X0:X1] = True
k = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 35))
med = cv2.morphologyEx(im.astype(np.uint8), cv2.MORPH_CLOSE, k).astype(np.float32)   # background without dark strokes
diff = (med - im).max(2); sat = im.max(2) - im.min(2)
tmask = box & ((diff > 4) | (sat > 12))
mask = cv2.dilate(tmask.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & box
# ---- clean background: diagonal (chevron-aligned) interpolation
def fill(img, mask):
    out = img.copy(); ys, xs = np.where(mask)
    for y, x in zip(ys, xs):
        best = None; single = None
        for dy, dx in ((1, 1), (1, -1)):
            ends = []
            for s in (1, -1):
                k = 1
                while k < 200:
                    yy, xx = y+s*dy*k, x+s*dx*k
                    if not (5 <= yy < H-5 and 5 <= xx < W-5): break
                    if not mask[yy, xx]: ends.append((k, img[yy, xx])); break
                    k += 1
            if len(ends) == 2:
                (k1, c1), (k2, c2) = ends; err = np.abs(c1-c2).sum() + 0.02*(k1+k2)
                if best is None or err < best[0]: best = (err, (c1*k2 + c2*k1)/(k1+k2))
            elif len(ends) == 1 and (single is None or ends[0][0] < single[0]): single = ends[0]
        if best is not None: out[y, x] = best[1]
        elif single is not None: out[y, x] = single[1]
    m = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
    return out*(1-m) + cv2.GaussianBlur(out, (0, 0), 0.6)*m
bg = fill(im, mask)
# ---- text layer: colour + alpha (un-mixed against the clean background)
C = np.zeros_like(im)
yy = np.arange(H)[:, None]
C[:] = (102, 102, 102)
C[(yy >= 190) & (yy < 270)[:, :1].repeat(W, 1) if False else np.broadcast_to((yy >= 190) & (yy < 270), (H, W))] = (51, 51, 51)
C[np.broadcast_to((yy >= 280) & (yy < 355), (H, W))] = (32, 105, 188)
blue = (im[..., 2] - im[..., 0] > 25) & np.broadcast_to(yy >= 390, (H, W))
C[blue] = (45, 172, 238)
den = np.maximum(np.abs(C - bg).max(2), 1)
alpha = np.clip(np.abs(im - bg).max(2)/den, 0, 1)*mask
# ---- compose: clean background + shifted text + QR
out = bg.copy()
a_s = np.roll(alpha, DY, axis=0); C_s = np.roll(C, DY, axis=0)
out = C_s*a_s[..., None] + out*(1-a_s[..., None])
from PIL import ImageDraw, ImageFilter
PAD = 13
qr = Image.open('v9/qr.png').convert('RGB').crop((14, 16, 279, 280))          # trim the stray border lines
inner = QR_S - 2*PAD
qr = qr.resize((inner, inner), Image.LANCZOS)
card = Image.new('L', (W, H)); ImageDraw.Draw(card).rounded_rectangle((QR_X, QR_Y, QR_X+QR_S, QR_Y+QR_S), 8, fill=255)
shadow = np.asarray(card.filter(ImageFilter.GaussianBlur(6)), np.float32)/255
shadow = np.roll(np.roll(shadow, 3, 0), 1, 1)*0.10
out = out*(1-shadow[..., None])
cm = np.asarray(card, np.float32)[..., None]/255
out = out*(1-cm) + 255*cm
out[QR_Y+PAD:QR_Y+PAD+inner, QR_X+PAD:QR_X+PAD+inner] = np.asarray(qr, np.float32)
qa = np.zeros((QR_S, QR_S))
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save('v9/final.png')
# checks
val, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(out[QR_Y-10:QR_Y+qa.shape[0]+10, QR_X-10:QR_X+qa.shape[1]+10], cv2.COLOR_RGB2BGR))
print('QR in final decodes to:', val)
print('right side unchanged:', np.abs(out[:, 730:].astype(int) - im[:, 730:].astype(int)).max())
