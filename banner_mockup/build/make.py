import sys, os, json, numpy as np, pymupdf
from PIL import Image, ImageFilter
W = os.path.dirname(os.path.abspath(__file__)) + '/../'
OUT = W + 'out/'; os.makedirs(OUT, exist_ok=True)
SCALE = 2.0                       # 3401pt -> ~6800px
F = SCALE/1.5
src = W + 'src/banner.pdf'
IMG = W + 'imgs/'

# xref -> (name, extracted image, smask or None, glow colour)
LOGOS = {
 273: ('eptc', 'i-056.png', None,        (255, 110, 20)),
 274: ('ieee', 'i-058.png', None,        (0, 150, 230)),
 275: ('eps',  'i-059.png', None,        (0, 120, 215)),
 217: ('lam',  'i-000.png', 'i-001.png', (40, 150, 255)),
}

doc = pymupdf.open(src); page = doc[0]
boxes = {i['xref']: i['bbox'] for i in page.get_image_info(xrefs=True) if i['xref'] in LOGOS}
for x in LOGOS: page.delete_image(x)            # base without the 4 logos
pix = page.get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE), alpha=False)
base = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).convert('RGBA')
H, Wd = pix.height, pix.width
print('page px', Wd, H)

def blur(a, r): return np.asarray(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)/255
def dilate(a, n):
    im = Image.fromarray((a*255).astype(np.uint8))
    while n > 0:
        k = min(n, 6); im = im.filter(ImageFilter.MaxFilter(2*k+1 if 2*k+1 <= 13 else 13)); n -= k
    return np.asarray(im, np.float32)/255

def logo_rgba(fn, smask, w, h):
    im = Image.open(IMG+fn).convert('RGB')
    if smask:
        a = Image.open(IMG+smask).convert('L')
        rgba = im.convert('RGBA'); rgba.putalpha(a)
    else:  # key out white background, un-premultiply colour
        c = np.asarray(im, np.float32)
        a = np.clip((243 - c.min(2)) / 80.0, 0, 1)
        col = np.where(a[..., None] > 0.01, (c - (1 - a[..., None]) * 255) / np.maximum(a[..., None], 1e-3), 255)
        rgba = Image.fromarray(np.dstack([np.clip(col, 0, 255), a*255]).astype(np.uint8), 'RGBA')
    return rgba.resize((w, h), Image.LANCZOS)

layers = {}
glow_canvas = np.zeros((H, Wd, 4), np.float32)   # premultiplied rgb + a
for xref, (name, fn, sm, gcol) in LOGOS.items():
    x0, y0, x1, y1 = [v*SCALE for v in boxes[xref]]
    w, h = round(x1-x0), round(y1-y0); X, Y = round(x0), round(y0)
    logo = logo_rgba(fn, sm, w, h)
    L = np.asarray(logo, np.float32)/255
    A = L[..., 3]
    # crop to content
    ys, xs = np.where(A > 0.05); cy0, cy1, cx0, cx1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
    L = L[cy0:cy1, cx0:cx1]; A = L[..., 3]; X += cx0; Y += cy0; h, w = A.shape
    PAD = int(340*F)
    P = lambda a: np.pad(a, ((PAD, PAD), (PAD, PAD)) + ((0, 0),)*(a.ndim-2))
    Ap = P(A); rgb = P(L[..., :3])
    depth, bev_r, bev_k, sh_off, sh_blur = {'eptc': (14, 2.2, 0.55, 22, 14), 'lam': (8, 1.5, 0.40, 16, 11),
                                            'ieee': (3, 0.8, 0.10, 9, 6), 'eps': (4, 0.8, 0.18, 10, 7)}[name]
    depth, bev_r, sh_off, sh_blur = round(depth*F), bev_r*F, round(sh_off*F), sh_blur*F
    # --- face bevel / lighting ---
    hgt = blur(Ap, bev_r)
    gy, gx = np.gradient(hgt)
    shade = -(gx*-0.7 + gy*-0.7)/(0.12*bev_r/2.2)            # light from top-left
    shade = np.clip(shade, -1, 1) * (Ap > 0)
    face = rgb.copy()
    hi = np.clip(shade, 0, 1)[..., None]*bev_k; lo = np.clip(-shade, 0, 1)[..., None]*bev_k*0.8
    face = face + (1-face)*hi; face = face*(1-lo)
    # gentle top-down gloss
    yy = np.linspace(1, 0, face.shape[0])[:, None, None]
    face = np.clip(face + (1-face)*0.10*yy, 0, 1)
    if name == 'lam':                          # black face: lift edges so it reads as 3D
        face = np.clip(rgb + 0.42*np.clip(shade, 0, 1)[..., None] + 0.07, 0, 1)
    face_img = np.dstack([face, Ap])
    # --- side (extrusion) colour: darker version of the face colour ---
    side = {'eptc': rgb*0.42, 'lam': np.full_like(rgb, 0.20)}.get(name, rgb*0.62)
    side_img = np.dstack([side, Ap])
    # --- LED halo (glow on the wall behind) ---
    core = dilate(Ap, round(4*F))
    g = np.clip(blur(core, 9*F)*1.0 + blur(core, 30*F)*0.8 + blur(core, 60*F)*0.35, 0, 1)
    g = 1 - np.exp(-2.2*g)                     # soft LED fall-off
    # --- contact shadow ---
    sh = blur(np.roll(np.roll(Ap, sh_off, 0), int(sh_off*0.75), 1), sh_blur)*0.42
    # write glow + shadow into base surface (premultiplied over)
    sx, sy = X-PAD, Y-PAD
    gc = np.array(gcol, np.float32)/255
    gl = np.zeros(Ap.shape + (4,), np.float32); gl[..., :3] = gc*g[..., None]*0.9; gl[..., 3] = g*0.9
    shl = np.zeros_like(gl); shl[..., 3] = sh; shl[..., :3] = 0.05*sh[..., None]
    for lay in (gl, shl):
        ox0, oy0 = max(0, -sx), max(0, -sy)
        ox1, oy1 = min(lay.shape[1], Wd-sx), min(lay.shape[0], H-sy)
        lay = lay[oy0:oy1, ox0:ox1]
        reg = glow_canvas[sy+oy0:sy+oy1, sx+ox0:sx+ox1]
        reg[:] = lay + reg*(1-lay[..., 3:4])
    layers[name] = dict(x=int(sx), y=int(sy), w=int(Ap.shape[1]), h=int(Ap.shape[0]), depth=int(depth))
    Image.fromarray((face_img*255).astype(np.uint8), 'RGBA').save(OUT+f'{name}_face.png')
    Image.fromarray((side_img*255).astype(np.uint8), 'RGBA').save(OUT+f'{name}_side.png')

# composite surface = base with glow/shadow
B = np.asarray(base, np.float32)/255
# light only the blank (near-white) banner surface, so other artwork/text stays untouched
lum = B[..., :3].min(2)
m = np.clip((lum - 0.80)/0.15, 0, 1)[..., None]
glow_canvas = glow_canvas*m
B[..., :3] = glow_canvas[..., :3] + B[..., :3]*(1-glow_canvas[..., 3:4])
surface = Image.fromarray((np.clip(B, 0, 1)*255).astype(np.uint8), 'RGBA')
surface.convert('RGB').save(OUT+'surface.png')
json.dump(dict(W=Wd, H=H, layers=layers), open(OUT+'layers.json', 'w'), indent=1)

# flat (front elevation) 3D composite: extrusion down-right, face at original position
flat = surface.copy()
for name, d in layers.items():
    face = Image.open(OUT+f'{name}_face.png'); side = Image.open(OUT+f'{name}_side.png')
    sa = np.asarray(side, np.float32)/255
    for k in range(d['depth'], 0, -1):
        t = k/d['depth']; s = sa.copy(); s[..., :3] *= (1 - 0.35*t)      # darker further back
        flat.alpha_composite(Image.fromarray((s*255).astype(np.uint8), 'RGBA'), (d['x']+round(k*0.75), d['y']+k))
    flat.alpha_composite(face, (d['x'], d['y']))
flat.convert('RGB').save(OUT+'EPTC2026_banner_3D_front.png', optimize=True)
print(layers)
