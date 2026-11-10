# 3D pop-up logos + LED halo for EPTC 2026 banner v4 (front-view composite + layers for perspective mock-ups)
import os, json, numpy as np, pymupdf
from PIL import Image, ImageFilter
W = os.path.dirname(os.path.abspath(__file__)) + '/../'
OUT = W + 'out/'; os.makedirs(OUT, exist_ok=True)
SCALE = 2.0; F = SCALE/1.5
SRC = W + 'src/banner.pdf'
# logo -> constituent image xrefs (drawn in order), LED colour
LOGOS = {
 'eptc': ([414], (255, 110, 20)),
 'ieee': ([243, 245], (0, 150, 230)),
 'eps':  ([244], (0, 120, 215)),
 'lam':  ([162], (40, 150, 255)),
}
doc = pymupdf.open(SRC); page = doc[0]
info = {i['xref']: i['bbox'] for i in page.get_image_info(xrefs=True)}
def img_rgba(xr):
    pm = pymupdf.Pixmap(doc, xr)
    if pm.alpha: pm = pymupdf.Pixmap(pm, 0)
    if pm.colorspace and pm.colorspace.n != 3: pm = pymupdf.Pixmap(pymupdf.csRGB, pm)
    rgb = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[..., :3].astype(np.float32)
    sm = doc.xref_get_key(xr, 'SMask')
    if sm[0] == 'xref':
        m = pymupdf.Pixmap(doc, int(sm[1].split()[0]))
        a = np.frombuffer(m.samples, np.uint8).reshape(m.height, m.width).astype(np.float32)/255
        if a.shape != rgb.shape[:2]: a = np.asarray(Image.fromarray((a*255).astype(np.uint8)).resize((rgb.shape[1], rgb.shape[0])), np.float32)/255
        col = rgb
    else:                                   # opaque white box: key the white out and un-premultiply
        a = np.clip((243 - rgb.min(2))/80.0, 0, 1)
        col = np.where(a[..., None] > 0.01, (rgb - (1-a[..., None])*255)/np.maximum(a[..., None], 1e-3), 255)
    return np.dstack([np.clip(col, 0, 255), a*255]).astype(np.uint8)
RGBA = {xr: img_rgba(xr) for parts, _ in LOGOS.values() for xr in parts}   # read before deleting
# --- base page without the four logos ---
for parts, _ in LOGOS.values():
    for xr in parts: page.delete_image(xr)
pix = page.get_pixmap(matrix=pymupdf.Matrix(SCALE, SCALE), alpha=False)
base = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).convert('RGBA'); H, Wd = pix.height, pix.width
print('page px', Wd, H)
def blur(a, r): return np.asarray(Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)/255
def dilate(a, n):
    im = Image.fromarray((a*255).astype(np.uint8))
    while n > 0: k = min(n, 6); im = im.filter(ImageFilter.MaxFilter(2*k+1)); n -= k
    return np.asarray(im, np.float32)/255
layers = {}; glow_canvas = np.zeros((H, Wd, 4), np.float32)
PARAM = {'eptc': (14, 2.2, 0.55, 22, 14), 'lam': (8, 1.5, 0.40, 16, 11), 'ieee': (3, 0.8, 0.10, 9, 6), 'eps': (4, 0.8, 0.18, 10, 7)}
for name, (parts, gcol) in LOGOS.items():
    bb = [min(info[x][0] for x in parts), min(info[x][1] for x in parts), max(info[x][2] for x in parts), max(info[x][3] for x in parts)]
    X, Y = round(bb[0]*SCALE), round(bb[1]*SCALE); w, h = round((bb[2]-bb[0])*SCALE), round((bb[3]-bb[1])*SCALE)
    canvas = Image.new('RGBA', (w, h))
    for xr in parts:
        b = info[xr]; im = Image.fromarray(RGBA[xr], 'RGBA').resize((round((b[2]-b[0])*SCALE), round((b[3]-b[1])*SCALE)), Image.LANCZOS)
        canvas.alpha_composite(im, (round(b[0]*SCALE)-X, round(b[1]*SCALE)-Y))
    L = np.asarray(canvas, np.float32)/255; A = L[..., 3]
    ys, xs = np.where(A > 0.05); cy0, cy1, cx0, cx1 = ys.min(), ys.max()+1, xs.min(), xs.max()+1
    L = L[cy0:cy1, cx0:cx1]; A = L[..., 3]; X += cx0; Y += cy0
    PAD = int(340*F)
    Pd = lambda a: np.pad(a, ((PAD, PAD), (PAD, PAD)) + ((0, 0),)*(a.ndim-2))
    Ap = Pd(A); rgb = Pd(L[..., :3])
    depth, bev_r, bev_k, sh_off, sh_blur = PARAM[name]
    depth, bev_r, sh_off, sh_blur = round(depth*F), bev_r*F, round(sh_off*F), sh_blur*F
    gy, gx = np.gradient(blur(Ap, bev_r))
    shade = np.clip(-(gx*-0.7 + gy*-0.7)/(0.12*bev_r/2.2), -1, 1)*(Ap > 0)
    face = rgb + (1-rgb)*np.clip(shade, 0, 1)[..., None]*bev_k
    face = face*(1-np.clip(-shade, 0, 1)[..., None]*bev_k*0.8)
    yy = np.linspace(1, 0, face.shape[0])[:, None, None]; face = np.clip(face + (1-face)*0.10*yy, 0, 1)
    if name == 'lam': face = np.clip(rgb + 0.42*np.clip(shade, 0, 1)[..., None] + 0.07, 0, 1)
    side = {'eptc': rgb*0.42, 'lam': np.full_like(rgb, 0.20)}.get(name, rgb*0.62)
    core = dilate(Ap, round(4*F))
    g = np.clip(blur(core, 9*F) + blur(core, 30*F)*0.8 + blur(core, 60*F)*0.35, 0, 1); g = 1-np.exp(-2.2*g)
    sh = blur(np.roll(np.roll(Ap, sh_off, 0), int(sh_off*0.75), 1), sh_blur)*0.42
    sx, sy = X-PAD, Y-PAD
    gl = np.zeros(Ap.shape+(4,), np.float32); gl[..., :3] = (np.array(gcol)/255)*g[..., None]*0.9; gl[..., 3] = g*0.9
    shl = np.zeros_like(gl); shl[..., 3] = sh; shl[..., :3] = 0.05*sh[..., None]
    for lay in (gl, shl):
        ox0, oy0 = max(0, -sx), max(0, -sy); ox1, oy1 = min(lay.shape[1], Wd-sx), min(lay.shape[0], H-sy)
        lay = lay[oy0:oy1, ox0:ox1]; reg = glow_canvas[sy+oy0:sy+oy1, sx+ox0:sx+ox1]; reg[:] = lay + reg*(1-lay[..., 3:4])
    layers[name] = dict(x=int(sx), y=int(sy), w=int(Ap.shape[1]), h=int(Ap.shape[0]), depth=int(depth))
    Image.fromarray((np.dstack([face, Ap])*255).astype(np.uint8), 'RGBA').save(OUT+f'{name}_face.png')
    Image.fromarray((np.dstack([side, Ap])*255).astype(np.uint8), 'RGBA').save(OUT+f'{name}_side.png')
B = np.asarray(base, np.float32)/255
m = np.clip((B[..., :3].min(2) - 0.70)/0.15, 0, 1)[..., None]      # LED light only on light, empty surface
gc = glow_canvas*m
B[..., :3] = gc[..., :3] + B[..., :3]*(1-gc[..., 3:4])
surface = Image.fromarray((np.clip(B, 0, 1)*255).astype(np.uint8), 'RGBA'); surface.convert('RGB').save(OUT+'surface.png')
json.dump(dict(W=Wd, H=H, layers=layers), open(OUT+'layers.json', 'w'), indent=1)
flat = surface.copy()
for name, d in layers.items():
    face = Image.open(OUT+f'{name}_face.png'); sa = np.asarray(Image.open(OUT+f'{name}_side.png'), np.float32)/255
    for k in range(d['depth'], 0, -1):
        s = sa.copy(); s[..., :3] *= (1-0.35*k/d['depth'])
        flat.alpha_composite(Image.fromarray((s*255).astype(np.uint8), 'RGBA'), (d['x']+round(k*0.75), d['y']+k))
    flat.alpha_composite(face, (d['x'], d['y']))
flat.convert('RGB').save(OUT+'EPTC2026_banner_v4_3D_front.png', optimize=True)
print(layers)
